import os
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings
from app.database import get_setting

logger = logging.getLogger(__name__)

SUPPORTED_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}

class ComposioDriveService:
    last_error: Optional[str] = None
    last_auth_url: Optional[str] = None

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        return get_setting("composio_api_key") or settings.COMPOSIO_API_KEY

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.get_api_key())

    @classmethod
    def get_or_create_auth_url(cls, callback_url: Optional[str] = None) -> Optional[str]:
        api_key = cls.get_api_key()
        if not api_key:
            return None
        try:
            from composio import Composio
            composio_client = Composio(api_key=api_key)
            auth_configs = composio_client.auth_configs.list(toolkit_slugs=["googledrive"])
            items = auth_configs.items if hasattr(auth_configs, "items") else auth_configs
            ac_id = items[0].id if items else None
            
            if not ac_id:
                new_ac = composio_client.auth_configs.create(
                    toolkit="googledrive",
                    options={
                        "type": "use_composio_managed_auth",
                        "name": "Google Drive Managed Auth"
                    }
                )
                ac_id = new_ac.id

            cb = callback_url or "https://video-metadata.mutamtour.com/settings"
            link = composio_client.connected_accounts.link(
                user_id="default",
                auth_config_id=ac_id,
                callback_url=cb
            )
            cls.last_auth_url = link.redirect_url
            return link.redirect_url
        except Exception as e:
            logger.error(f"Error generating Composio auth link: {e}")
            return None

    @classmethod
    def check_connection_status(cls) -> Dict[str, Any]:
        api_key = cls.get_api_key()
        if not api_key:
            return {"connected": False, "status": "NO_API_KEY", "auth_url": None}
        try:
            from composio import Composio
            composio_client = Composio(api_key=api_key)
            accounts = composio_client.connected_accounts.list(toolkit_slugs=["googledrive"])
            items = accounts.items if hasattr(accounts, "items") else accounts
            active_acc = next((a for a in items if getattr(a, "status", "") == "ACTIVE"), None)
            
            if active_acc:
                cls.last_error = None
                return {"connected": True, "status": "ACTIVE", "account_id": active_acc.id, "auth_url": None}
            
            auth_url = cls.get_or_create_auth_url()
            current_status = items[0].status if items else "NOT_CONNECTED"
            cls.last_auth_url = auth_url
            cls.last_error = f"Google Drive belum terhubung aktif (status: {current_status}). Klik 'Hubungkan Google Drive' untuk otorisasi."
            return {"connected": False, "status": current_status, "auth_url": auth_url}
        except Exception as e:
            logger.error(f"Error checking Composio connection status: {e}")
            cls.last_error = f"Gagal mengecek status Composio: {e}"
            return {"connected": False, "status": "ERROR", "error": str(e), "auth_url": None}

    @classmethod
    async def list_files_recursive(cls, folder_id: str) -> List[Dict[str, Any]]:
        """
        Recursively traverse Google Drive folder and return all video and photo files.
        Uses Composio v3 tools.execute(slug="GOOGLEDRIVE_FIND_FILE", arguments=..., user_id="default").
        """
        api_key = cls.get_api_key()
        cls.last_error = None

        if not api_key:
            logger.info("Composio API key not set. Using test footage.")
            return cls._get_mock_drive_files(folder_id)

        try:
            from composio import Composio
            composio_client = Composio(api_key=api_key)

            # Check if active connection exists
            accounts = composio_client.connected_accounts.list(toolkit_slugs=["googledrive"])
            items = accounts.items if hasattr(accounts, "items") else accounts
            active_acc = next((a for a in items if getattr(a, "status", "") == "ACTIVE"), None)

            if not active_acc:
                auth_url = cls.get_or_create_auth_url()
                current_status = items[0].status if items else "NOT_CONNECTED"
                cls.last_error = f"Google Drive belum aktif (status: {current_status}). Silakan hubungkan akun Google Drive melalui link otorisasi: {auth_url}"
                logger.warning(cls.last_error)
                return cls._get_mock_drive_files(folder_id)
            
            query = f"'{folder_id}' in parents and trashed = false"
            logger.info(f"Querying Google Drive via Composio v3 for folder {folder_id} with account {active_acc.id}...")
            
            # Execute Composio v3 Tool
            result = composio_client.tools.execute(
                slug="GOOGLEDRIVE_FIND_FILE",
                arguments={"query": query},
                user_id="default",
                connected_account_id=active_acc.id,
                dangerously_skip_version_check=True
            )
            
            raw_items = []
            res_data = getattr(result, "data", result)
            if isinstance(res_data, dict):
                raw_items = res_data.get("files", []) or res_data.get("response_data", {}).get("files", [])
            elif isinstance(res_data, list):
                raw_items = res_data

            if raw_items:
                items_res = []
                for item in raw_items:
                    mime_type = item.get("mimeType", "")
                    name = item.get("name", "")
                    file_id = item.get("id")
                    
                    if mime_type == "application/vnd.google-apps.folder":
                        sub_files = await cls.list_files_recursive(file_id)
                        items_res.extend(sub_files)
                        continue

                    ext = os.path.splitext(name.lower())[1]
                    if ext in SUPPORTED_VIDEO_EXTS or ext in SUPPORTED_IMAGE_EXTS:
                        f_type = "video" if ext in SUPPORTED_VIDEO_EXTS else "image"
                        items_res.append({
                            "file_id": file_id,
                            "file_name": name,
                            "file_type": f_type,
                            "storage_url": item.get("webContentLink") or f"https://drive.google.com/uc?id={file_id}&export=download",
                            "thumbnail_url": item.get("thumbnailLink"),
                            "parent_folder": folder_id,
                            "created_time": item.get("createdTime")
                        })
                logger.info(f"Successfully retrieved {len(items_res)} media files from Google Drive via Composio!")
                return items_res
            else:
                logger.warning(f"No files found in folder {folder_id} via Composio.")
                return []

        except Exception as e:
            err_msg = str(e)
            logger.error(f"Composio execution error: {err_msg}")
            if "401" in err_msg or "Invalid API key" in err_msg:
                cls.last_error = f"API Key Composio '{api_key[:6]}...' ditolak server Composio (HTTP 401: Invalid API key). Pastikan menggunakan Project API Key dari dashboard Composio."
            elif "422" in err_msg or "INITIALIZING" in err_msg:
                auth_url = cls.get_or_create_auth_url()
                cls.last_error = f"Koneksi Google Drive belum selesai diotorisasi (INITIALIZING). Silakan klik link otorisasi: {auth_url}"
            else:
                cls.last_error = f"Composio error: {err_msg}"

        return cls._get_mock_drive_files(folder_id)

    @classmethod
    async def download_file_to_temp(cls, file_id: str, dest_path: str) -> bool:
        try:
            url = f"https://drive.google.com/uc?id={file_id}&export=download"
            async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code == 200:
                        with open(dest_path, "wb") as f:
                            async for chunk in response.aiter_bytes():
                                f.write(chunk)
                        return True
            return False
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            return False

    @classmethod
    def _get_mock_drive_files(cls, folder_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "file_id": f"drive_makkah_towaf_{folder_id[:4] if folder_id else '01'}_01",
                "file_name": "raw_makkah_towaf_01.mp4",
                "file_type": "video",
                "storage_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "thumbnail_url": "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?w=600&auto=format&fit=crop",
                "parent_folder": folder_id or "root_umrah_raw",
                "created_time": "2026-10-28T09:00:00Z"
            },
            {
                "file_id": f"drive_madinah_nabawi_{folder_id[:4] if folder_id else '02'}_02",
                "file_name": "raw_madinah_payung_nabawi.mp4",
                "file_type": "video",
                "storage_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                "thumbnail_url": "https://images.unsplash.com/photo-1565552645632-d725f8bfc19a?w=600&auto=format&fit=crop",
                "parent_folder": folder_id or "root_umrah_raw",
                "created_time": "2026-10-28T10:30:00Z"
            },
            {
                "file_id": f"drive_jabal_uhud_{folder_id[:4] if folder_id else '03'}_03",
                "file_name": "raw_ziarah_jabal_uhud.mp4",
                "file_type": "video",
                "storage_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
                "thumbnail_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=600&auto=format&fit=crop",
                "parent_folder": folder_id or "subfolder_madinah",
                "created_time": "2026-10-29T08:15:00Z"
            },
            {
                "file_id": f"drive_manasik_doa_{folder_id[:4] if folder_id else '04'}_04",
                "file_name": "raw_jamaah_doa_bersama.mp4",
                "file_type": "video",
                "storage_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4",
                "thumbnail_url": "https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?w=600&auto=format&fit=crop",
                "parent_folder": folder_id or "subfolder_manasik",
                "created_time": "2026-10-29T14:00:00Z"
            },
            {
                "file_id": f"drive_hotel_makkah_view_{folder_id[:4] if folder_id else '05'}_05",
                "file_name": "photo_hotel_tower_clock.jpg",
                "file_type": "image",
                "storage_url": "https://images.unsplash.com/photo-1564769625905-50e93615e769?w=1200&auto=format&fit=crop",
                "thumbnail_url": "https://images.unsplash.com/photo-1564769625905-50e93615e769?w=600&auto=format&fit=crop",
                "parent_folder": folder_id or "subfolder_hotel",
                "created_time": "2026-10-30T07:00:00Z"
            }
        ]
