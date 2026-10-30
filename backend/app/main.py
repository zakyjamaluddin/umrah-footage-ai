import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.database import init_db
from app.routers import files, scan, script, settings as settings_router
from app.services.scheduler_service import PollingSchedulerService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database & Background 5-Minute Scheduler
    logger.info("Initializing SQLite database...")
    init_db()
    
    logger.info("Starting background 24/7 polling scheduler...")
    try:
        PollingSchedulerService.start_scheduler()
    except Exception as e:
        logger.warning(f"Could not start background scheduler: {e}")
        
    yield
    # Shutdown
    logger.info("Application shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Sistem Analisa Metadata Video/Foto Umrah dari Google Drive via Composio & Gemini",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(files.router, prefix="/api")
app.include_router(scan.router, prefix="/api")
app.include_router(script.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")

# Static frontend serving for production VPS deployment
frontend_dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist_path):
    logger.info(f"Serving production frontend from {frontend_dist_path}")
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept /api routes
        if full_path.startswith("api/"):
            return None
        file_path = os.path.join(frontend_dist_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist_path, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "status": "online",
            "app": settings.PROJECT_NAME,
            "docs_url": "/docs",
            "mode": "api_only"
        }
