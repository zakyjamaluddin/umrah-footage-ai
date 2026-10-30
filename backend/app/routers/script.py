from fastapi import APIRouter, HTTPException
from app.models import AdsScriptAnalysisRequest, AdsScriptAnalysisResponse
from app.services.script_service import AdsScriptMatcherService

router = APIRouter(prefix="/script", tags=["script"])

@router.post("/analyze-match", response_model=AdsScriptAnalysisResponse)
async def analyze_and_match_script(request: AdsScriptAnalysisRequest):
    """
    Analyze ad script, break down into ~4-5 second scenes, 
    and match each segment to relevant Umrah footage in database.
    """
    if not request.script_text.strip():
        raise HTTPException(status_code=400, detail="Naskah iklan tidak boleh kosong.")
    
    response = await AdsScriptMatcherService.analyze_and_match(request)
    return response
