import os
import httpx
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
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
    
    # Inject reliable stream and thumbnail URLs
    for f in files:
        fid = f.get("file_id")
        if not f.get("thumbnail_url"):
            f["thumbnail_url"] = f"/api/files/{fid}/thumbnail"
        f["stream_url"] = f"/api/files/{fid}/stream"
        f["preview_url"] = f"https://drive.google.com/file/d/{fid}/preview"
        for s in f.get("scenes", []):
            s["stream_url"] = f["stream_url"]
            s["preview_url"] = f["preview_url"]

    return {
        "total": len(files),
        "items": files
    }

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
        fid = s.get("file_id")
        s["stream_url"] = f"/api/files/{fid}/stream"
        s["preview_url"] = f"https://drive.google.com/file/d/{fid}/preview"
        s["thumbnail_url"] = f"/api/files/{fid}/thumbnail"
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

@router.get("/{file_id}/thumbnail")
async def get_thumbnail(file_id: str):
    """Proxy Google Drive thumbnail to bypass CORS/hotlinking restrictions."""
    thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w800"
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        try:
            r = await client.get(thumb_url)
            if r.status_code == 200 and len(r.content) > 500:
                return Response(
                    content=r.content,
                    media_type=r.headers.get("content-type", "image/jpeg"),
                    headers={"Cache-Control": "public, max-age=86400"}
                )
        except Exception:
            pass
        
        # Fallback to direct download
        direct_url = f"https://drive.google.com/uc?id={file_id}&export=download"
        try:
            r = await client.get(direct_url)
            return Response(
                content=r.content,
                media_type=r.headers.get("content-type", "image/jpeg"),
                headers={"Cache-Control": "public, max-age=86400"}
            )
        except Exception as e:
            raise HTTPException(status_code=404, detail="Thumbnail unavailable")

@router.get("/{file_id}/stream")
async def stream_file(file_id: str, request: Request):
    """Proxy streaming video/media with HTTP Range (206) support."""
    target_url = f"https://drive.google.com/uc?id={file_id}&export=download"
    range_header = request.headers.get("range")
    req_headers = {}
    if range_header:
        req_headers["Range"] = range_header

    client = httpx.AsyncClient(follow_redirects=True, timeout=60.0)
    try:
        req = client.build_request("GET", target_url, headers=req_headers)
        r = await client.send(req, stream=True)

        async def stream_generator():
            try:
                async for chunk in r.aiter_bytes(chunk_size=128 * 1024):
                    yield chunk
            finally:
                await r.aclose()
                await client.aclose()

        resp_headers = {
            "Accept-Ranges": "bytes",
            "Content-Disposition": "inline",
            "Access-Control-Allow-Origin": "*",
        }
        if "content-length" in r.headers:
            resp_headers["Content-Length"] = r.headers["content-length"]
        if "content-range" in r.headers:
            resp_headers["Content-Range"] = r.headers["content-range"]

        content_type = r.headers.get("content-type", "video/mp4")
        if "text/html" in content_type:
            content_type = "video/mp4"

        return StreamingResponse(
            stream_generator(),
            status_code=r.status_code,
            headers=resp_headers,
            media_type=content_type
        )
    except Exception as e:
        await client.aclose()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}")
def get_file(file_id: str):
    file_data = get_file_by_id(file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="File tidak ditemukan.")
    file_data["stream_url"] = f"/api/files/{file_id}/stream"
    file_data["preview_url"] = f"https://drive.google.com/file/d/{file_id}/preview"
    file_data["thumbnail_url"] = f"/api/files/{file_id}/thumbnail"
    return file_data
