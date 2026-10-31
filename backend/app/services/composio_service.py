import os
import logging
from typing import List, Dict, Any, Optional, Set
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
            auth_configs = composio_client.auth_configs.list(toolkit_slug="googledrive")
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
    async def list_files_recursive(cls, folder_id: str, visited: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
        """
        Recursively traverse Google Drive folder (and shortcuts) and return all video and photo files.
        Uses Composio v3 tools.execute(slug="GOOGLEDRIVE_FIND_FILE", arguments=..., user_id="default").
        """
        if visited is None:
            visited = set()
        if folder_id in visited:
            return []
        visited.add(folder_id)

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
            
            # Execute Composio v3 Tool requesting all fields so shortcutDetails are populated
            result = composio_client.tools.execute(
                slug="GOOGLEDRIVE_FIND_FILE",
                arguments={
                    "query": query,
                    "fields": "*"
                },
                user_id="default",
                connected_account_id=active_acc.id,
                dangerously_skip_version_check=True
            )
            
            raw_items = []
            if isinstance(result, dict):
                raw_items = result.get("data", {}).get("files", []) or result.get("files", []) or result.get("response_data", {}).get("files", [])
            elif hasattr(result, "data"):
                d = result.data
                raw_items = d.get("files", []) if isinstance(d, dict) else getattr(d, "files", [])

            if raw_items:
                items_res = []
                for item in raw_items:
                    mime_type = item.get("mimeType", "")
                    name = item.get("name", "")
                    file_id = item.get("id")
                    
                    # 1. Folder -> Recurse
                    if mime_type == "application/vnd.google-apps.folder":
                        sub_files = await cls.list_files_recursive(file_id, visited=visited)
                        items_res.extend(sub_files)
                        continue

                    # 2. Shortcut -> Resolve target
                    if mime_type == "application/vnd.google-apps.shortcut":
                        shortcut_details = item.get("shortcutDetails", {})
                        target_id = shortcut_details.get("targetId")
                        target_mime = shortcut_details.get("targetMimeType", "")
                        if target_id:
                            if target_mime == "application/vnd.google-apps.folder":
                                sub_files = await cls.list_files_recursive(target_id, visited=visited)
                                items_res.extend(sub_files)
                                continue
                            elif any(target_mime.startswith(p) for p in ["video/", "image/"]):
                                ext = os.path.splitext(name.lower())[1]
                                f_type = "video" if ("video" in target_mime or ext in SUPPORTED_VIDEO_EXTS) else "image"
                                items_res.append({
                                    "file_id": target_id,
                                    "file_name": name,
                                    "file_type": f_type,
                                    "storage_url": item.get("webContentLink") or f"https://drive.google.com/uc?id={target_id}&export=download",
                                    "thumbnail_url": item.get("thumbnailLink"),
                                    "parent_folder": folder_id,
                                    "created_time": item.get("createdTime")
                                })
                                continue

                    # 3. Direct Video or Image File
                    ext = os.path.splitext(name.lower())[1]
                    is_video = ext in SUPPORTED_VIDEO_EXTS or (mime_type and mime_type.startswith("video/"))
                    is_image = ext in SUPPORTED_IMAGE_EXTS or (mime_type and mime_type.startswith("image/"))

                    if is_video or is_image:
                        f_type = "video" if is_video else "image"
                        items_res.append({
                            "file_id": file_id,
                            "file_name": name,
                            "file_type": f_type,
                            "storage_url": item.get("webContentLink") or f"https://drive.google.com/uc?id={file_id}&export=download",
                            "thumbnail_url": item.get("thumbnailLink"),
                            "parent_folder": folder_id,
                            "created_time": item.get("createdTime")
                        })

                logger.info(f"Retrieved {len(items_res)} media files from folder {folder_id} (and its subfolders/shortcuts).")
                return items_res
            else:
                logger.info(f"No direct items in folder {folder_id}.")
                return []

        except Exception as e:
            err_msg = str(e)
            logger.error(f"Composio execution error for folder {folder_id}: {err_msg}")
            if "401" in err_msg or "Invalid API key" in err_msg:
                cls.last_error = f"API Key Composio '{api_key[:6]}...' ditolak server Composio (HTTP 401). Pastikan menggunakan Project Access Key."
            else:
                cls.last_error = f"Composio error: {err_msg}"

        return []

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
            }
        ]
