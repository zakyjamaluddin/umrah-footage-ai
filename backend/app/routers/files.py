from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.database import get_all_files, get_file_by_id, get_all_scenes

router = APIRouter(prefix="/files", tags=["files"])

@router.get("/")
def list_files(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    file_type: Optional[str] = None
):
    files = get_all_files(limit=limit, offset=offset)
    if file_type:
        files = [f for f in files if f.get("file_type") == file_type]
    return {
        "total": len(files),
        "items": files
    }

@router.get("/{file_id}")
def get_file(file_id: str):
    file_data = get_file_by_id(file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="File tidak ditemukan.")
    return file_data

@router.get("/scenes/all")
def list_scenes(
    location: Optional[str] = None,
    mood: Optional[str] = None,
    tag: Optional[str] = None,
    suitability: Optional[str] = None
):
    scenes = get_all_scenes()
    filtered = []
    for s in scenes:
        if location and location.lower() not in s.get("location", "").lower():
            continue
        if mood and mood.lower() != s.get("mood", "").lower():
            continue
        if tag and not any(tag.lower() in t.lower() for t in s.get("tags", [])):
            continue
        if suitability and not any(suitability.lower() in st.lower() for st in s.get("suitability", [])):
            continue
        filtered.append(s)
    return {
        "total": len(filtered),
        "items": filtered
    }
