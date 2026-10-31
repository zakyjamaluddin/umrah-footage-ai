from fastapi import APIRouter
from app.models import SettingsUpdateRequest
from app.database import get_setting, set_setting, get_all_settings
from app.config import settings
from app.services.scheduler_service import PollingSchedulerService
from app.services.composio_service import ComposioDriveService

router = APIRouter(prefix="/settings", tags=["settings"])

def mask_key(k: str) -> str:
    if not k or len(k) < 8:
        return "Not Set" if not k else "********"
    return k[:4] + "..." + k[-4:]

@router.get("/")
def get_current_settings():
    composio_key = get_setting("composio_api_key") or settings.COMPOSIO_API_KEY
    gemini_key = get_setting("gemini_api_key") or settings.GEMINI_API_KEY
    folder_id = get_setting("google_drive_folder_id") or settings.GOOGLE_DRIVE_FOLDER_ID or ""
    interval = int(get_setting("polling_interval_minutes", str(settings.POLLING_INTERVAL_MINUTES)))
    auto_polling = get_setting("auto_polling_enabled", "true").lower() == "true"

    conn_status = ComposioDriveService.check_connection_status()

    return {
        "google_drive_folder_id": folder_id,
        "composio_api_key_set": bool(composio_key),
        "composio_api_key_masked": mask_key(composio_key),
        "gemini_api_key_set": bool(gemini_key),
        "gemini_api_key_masked": mask_key(gemini_key),
        "polling_interval_minutes": interval,
        "auto_polling_enabled": auto_polling,
        "gdrive_connected": conn_status.get("connected", False),
        "gdrive_status": conn_status.get("status", "NOT_CONFIGURED"),
        "gdrive_auth_url": conn_status.get("auth_url")
    }

@router.get("/gdrive-auth-url")
def get_gdrive_auth_url():
    url = ComposioDriveService.get_or_create_auth_url()
    return {"auth_url": url}

@router.post("/")
def update_settings(payload: SettingsUpdateRequest):
    if payload.google_drive_folder_id is not None:
        set_setting("google_drive_folder_id", payload.google_drive_folder_id.strip())
    
    if payload.composio_api_key is not None and payload.composio_api_key.strip():
        set_setting("composio_api_key", payload.composio_api_key.strip())
        
    if payload.gemini_api_key is not None and payload.gemini_api_key.strip():
        set_setting("gemini_api_key", payload.gemini_api_key.strip())
        
    if payload.polling_interval_minutes is not None and payload.polling_interval_minutes >= 1:
        set_setting("polling_interval_minutes", str(payload.polling_interval_minutes))
        PollingSchedulerService.update_interval(payload.polling_interval_minutes)

    if payload.auto_polling_enabled is not None:
        set_setting("auto_polling_enabled", "true" if payload.auto_polling_enabled else "false")

    return {
        "status": "success",
        "message": "Pengaturan berhasil diperbarui."
    }
