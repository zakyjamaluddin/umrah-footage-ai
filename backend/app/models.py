from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SceneMetadata(BaseModel):
    start_time: float = Field(..., description="Waktu mulai scene dalam detik")
    end_time: float = Field(..., description="Waktu selesai scene dalam detik")
    location: str = Field(..., description="Lokasi terdeteksi, misal: Masjidil Haram - Mataf, Jabal Uhud")
    visual_description: str = Field(..., description="Deskripsi visual mendalam tentang apa yang terlihat")
    tags: List[str] = Field(default_factory=list, description="Tag relevan seperti crowd, kabah, close-up, tawaf")
    mood: str = Field("khusyuk", description="Suasana/mood visual: khusyuk, haru, megah, syahdu, ceria, dinamis")
    pacing: str = Field("slow", description="Tempo visual: slow, medium, fast")
    suitability: List[str] = Field(default_factory=list, description="Kesesuaian segmen: opening, emotional_hook, broll, narration, closing")

class FileMetadata(BaseModel):
    file_id: str = Field(..., description="ID unik file Google Drive")
    file_name: str = Field(..., description="Nama file, contoh: raw_makkah_towaf_01.mp4")
    file_type: str = Field("video", description="video atau image")
    storage_url: str = Field(..., description="URL akses / download / streaming file")
    duration_seconds: float = Field(0.0, description="Durasi video dalam detik (0 jika foto)")
    parent_folder: Optional[str] = None
    thumbnail_url: Optional[str] = None
    scenes: List[SceneMetadata] = Field(default_factory=list)
    created_at: Optional[str] = None
    analyzed_at: Optional[str] = None

class QueueTask(BaseModel):
    id: Optional[int] = None
    file_id: str
    file_name: str
    file_type: str
    status: str = "PENDING"  # PENDING, DOWNLOADING, ANALYZING, COMPLETED, FAILED
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# Ads Script Matching Models
class MatchedScene(BaseModel):
    file_id: str
    file_name: str
    storage_url: str
    start_time: float
    end_time: float
    location: str
    visual_description: str
    tags: List[str]
    mood: str
    pacing: str
    suitability: List[str]
    relevance_score: float = 0.0
    reason: str = ""

class ScriptSegment(BaseModel):
    segment_index: int
    estimated_start: float
    estimated_end: float
    duration: float
    narration_text: str
    topic: str
    visual_requirement: str
    recommended_mood: str
    matched_scenes: List[MatchedScene] = Field(default_factory=list)

class AdsScriptAnalysisRequest(BaseModel):
    script_text: str
    target_duration_per_scene: float = 4.5
    preferred_mood: Optional[str] = None

class AdsScriptAnalysisResponse(BaseModel):
    total_estimated_duration: float
    segments: List[ScriptSegment]
    summary: str

class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    composio_api_key: Optional[str] = None
    google_drive_folder_id: Optional[str] = None
    polling_interval_minutes: Optional[int] = None
    auto_polling_enabled: Optional[bool] = None
