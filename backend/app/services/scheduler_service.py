import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from app.config import settings
from app.database import (
    get_setting,
    get_pending_tasks,
    update_queue_status,
    save_file_metadata,
    enqueue_file,
    get_file_by_id,
    get_all_queue_tasks
)
from app.services.composio_service import ComposioDriveService
from app.services.gemini_service import GeminiAnalyzerService
from app.services.vector_service import SceneVectorIndex

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

class PollingSchedulerService:
    last_poll_time: Optional[datetime] = None
    is_scanning: bool = False
    is_processing_queue: bool = False

    @classmethod
    def start_scheduler(cls):
        if not scheduler.running:
            minutes = int(get_setting("polling_interval_minutes", str(settings.POLLING_INTERVAL_MINUTES)))
            scheduler.add_job(
                cls.poll_drive_folder,
                'interval',
                minutes=minutes,
                id='gdrive_poll_job',
                replace_existing=True
            )
            scheduler.start()
            logger.info(f"Background polling scheduler started (every {minutes} minutes).")

    @classmethod
    def update_interval(cls, minutes: int):
        if scheduler.running:
            scheduler.reschedule_job('gdrive_poll_job', trigger='interval', minutes=minutes)
            logger.info(f"Updated polling interval to {minutes} minutes.")

    @classmethod
    def poll_drive_folder(cls):
        """Background job triggered every 5 minutes."""
        asyncio.run(cls.scan_and_enqueue())

    @classmethod
    async def scan_and_enqueue(cls) -> Dict[str, Any]:
        """Scan Google Drive folder and enqueue new files."""
        if cls.is_scanning:
            return {"status": "already_scanning", "message": "Scan sedang berjalan..."}

        cls.is_scanning = True
        cls.last_poll_time = datetime.now()
        new_files_count = 0

        try:
            folder_id = get_setting("google_drive_folder_id") or settings.GOOGLE_DRIVE_FOLDER_ID
            if not folder_id:
                logger.warning("No Google Drive folder ID configured yet.")
                return {"status": "skipped", "message": "Folder ID belum diatur di Settings."}

            logger.info(f"Scanning Google Drive folder ID: {folder_id}...")
            drive_files = await ComposioDriveService.list_files_recursive(folder_id)

            for f in drive_files:
                file_id = f["file_id"]
                # Check if already processed in database
                existing_file = get_file_by_id(file_id)
                if not existing_file:
                    enqueue_file(file_id=file_id, file_name=f["file_name"], file_type=f["file_type"])
                    new_files_count += 1

            # Trigger queue processing immediately if new files were found
            if new_files_count > 0:
                asyncio.create_task(cls.process_queue_worker())

            return {
                "status": "success",
                "folder_id": folder_id,
                "total_found": len(drive_files),
                "new_enqueued": new_files_count,
                "scanned_at": cls.last_poll_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Error during folder poll: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            cls.is_scanning = False

    @classmethod
    async def process_queue_worker(cls):
        """Worker that consumes queued files and runs Gemini analysis."""
        if cls.is_processing_queue:
            return

        cls.is_processing_queue = True
        try:
            while True:
                tasks = get_pending_tasks(limit=5)
                if not tasks:
                    break

                for task in tasks:
                    file_id = task["file_id"]
                    file_name = task["file_name"]
                    file_type = task["file_type"]

                    try:
                        update_queue_status(file_id, "ANALYZING")
                        temp_dest = os.path.join(settings.STORAGE_DIR, f"temp_{file_id}_{file_name}")
                        
                        # Direct stream URL or sample storage url
                        storage_url = f"https://drive.google.com/uc?id={file_id}&export=download"

                        # Call Gemini Scene Analyzer
                        metadata = await GeminiAnalyzerService.analyze_media_file(
                            file_path=temp_dest if os.path.exists(temp_dest) else None,
                            file_name=file_name,
                            file_type=file_type,
                            file_id=file_id,
                            storage_url=storage_url
                        )

                        # Save to database
                        save_file_metadata(metadata)

                        # Index scenes for semantic vector search
                        for idx, scene in enumerate(metadata.scenes):
                            SceneVectorIndex.index_scene(
                                scene_id=hash(f"{file_id}_{idx}"),
                                scene_data=scene.model_dump()
                            )

                        # Clean up temp file if exists
                        if os.path.exists(temp_dest):
                            os.remove(temp_dest)

                        update_queue_status(file_id, "COMPLETED")
                        logger.info(f"Successfully processed {file_name} ({len(metadata.scenes)} scenes).")

                    except Exception as task_err:
                        logger.error(f"Failed processing {file_name}: {task_err}")
                        update_queue_status(file_id, "FAILED", str(task_err))

        finally:
            cls.is_processing_queue = False

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        queue = get_all_queue_tasks()
        pending = sum(1 for q in queue if q["status"] == "PENDING")
        analyzing = sum(1 for q in queue if q["status"] == "ANALYZING")
        completed = sum(1 for q in queue if q["status"] == "COMPLETED")
        failed = sum(1 for q in queue if q["status"] == "FAILED")

        interval = int(get_setting("polling_interval_minutes", str(settings.POLLING_INTERVAL_MINUTES)))

        return {
            "is_scanning": cls.is_scanning,
            "is_processing_queue": cls.is_processing_queue,
            "last_poll_time": cls.last_poll_time.isoformat() if cls.last_poll_time else None,
            "polling_interval_minutes": interval,
            "last_error": ComposioDriveService.last_error,
            "composio_auth_url": ComposioDriveService.last_auth_url or ComposioDriveService.get_or_create_auth_url(),
            "queue_counts": {
                "total": len(queue),
                "pending": pending,
                "analyzing": analyzing,
                "completed": completed,
                "failed": failed
            }
        }
