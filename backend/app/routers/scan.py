from fastapi import APIRouter, BackgroundTasks
from app.services.scheduler_service import PollingSchedulerService
from app.database import get_all_queue_tasks

router = APIRouter(prefix="/scan", tags=["scan"])

@router.post("/trigger")
async def trigger_scan(background_tasks: BackgroundTasks):
    """Manually trigger Google Drive scan and start processing queue."""
    result = await PollingSchedulerService.scan_and_enqueue()
    return result

@router.get("/status")
def get_scan_status():
    """Get status of background 5-minute polling and queue processing."""
    return PollingSchedulerService.get_status()

@router.get("/queue")
def list_queue():
    """Get all items currently in processing queue."""
    return {
        "items": get_all_queue_tasks()
    }
