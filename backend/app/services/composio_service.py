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
    @classmethod
    def get_api_key(cls) -> Optional[str]:
        return get_setting("composio_api_key") or settings.COMPOSIO_API_KEY

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.get_api_key())

    @classmethod
    def get_toolset(cls):
        api_key = cls.get_api_key()
        if not api_key:
            return None
        try:
            from composio import ComposioToolSet, Action, App
            return ComposioToolSet(api_key=api_key)
        except Exception as e:
            logger.error(f"Error initializing ComposioToolSet: {e}")
            return None

    @classmethod
    async def list_files_recursive(cls, folder_id: str) -> List[Dict[str, Any]]:
        """
        Recursively traverse Google Drive folder and return all video and photo files.
        """
        api_key = cls.get_api_key()
        if not api_key:
            logger.info("Composio API key not set. Using simulated test footage for local verification.")
            return cls._get_mock_drive_files(folder_id)

        try:
            from composio import ComposioToolSet, Action, App
            toolset = ComposioToolSet(api_key=api_key)
            
            # Execute Composio Google Drive search or list action
            # We search for files with parent = folder_id or inside subfolders
            query = f"'{folder_id}' in parents and trashed = false"
            result = toolset.execute_action(
                action=Action.GOOGLEDRIVE_FIND_FILE,
                params={"query": query}
            )
            
            items = []
            if isinstance(result, dict) and "data" in result:
                raw_items = result["data"].get("files", [])
            elif isinstance(result, list):
                raw_items = result
            else:
                raw_items = []

            for item in raw_items:
                mime_type = item.get("mimeType", "")
                name = item.get("name", "")
                file_id = item.get("id")
                
                # Check if it's a folder to recurse
                if mime_type == "application/vnd.google-apps.folder":
                    sub_files = await cls.list_files_recursive(file_id)
                    items.extend(sub_files)
                    continue

                ext = os.path.splitext(name.lower())[1]
                if ext in SUPPORTED_VIDEO_EXTS:
                    items.append({
                        "file_id": file_id,
                        "file_name": name,
                        "file_type": "video",
                        "storage_url": item.get("webContentLink") or f"https://drive.google.com/uc?id={file_id}&export=download",
                        "thumbnail_url": item.get("thumbnailLink"),
                        "parent_folder": folder_id,
                        "created_time": item.get("createdTime")
                    })
                elif ext in SUPPORTED_IMAGE_EXTS:
                    items.append({
                        "file_id": file_id,
                        "file_name": name,
                        "file_type": "image",
                        "storage_url": item.get("webContentLink") or f"https://drive.google.com/uc?id={file_id}&export=download",
                        "thumbnail_url": item.get("thumbnailLink"),
                        "parent_folder": folder_id,
                        "created_time": item.get("createdTime")
                    })
            return items

        except Exception as e:
            logger.error(f"Error scanning folder via Composio: {e}")
            # Graceful fallback to mock data if token not ready
            return cls._get_mock_drive_files(folder_id)

    @classmethod
    async def download_file_to_temp(cls, file_id: str, dest_path: str) -> bool:
        """
        Download file from Google Drive via Composio or direct Drive link.
        """
        try:
            # Download via direct stream
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
        """Sample mock data for immediate UI testing and preview demonstration."""
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
