import json
import logging
import math
from typing import List, Dict, Any, Optional
from app.config import settings
from app.database import get_setting
from app.models import AdsScriptAnalysisRequest, AdsScriptAnalysisResponse, ScriptSegment, MatchedScene
from app.services.vector_service import SceneVectorIndex

logger = logging.getLogger(__name__)

BREAKDOWN_PROMPT = """
Anda adalah AI Video Director & Editor Iklan profesional khusus biro perjalanan Umrah & Haji.
Tugas Anda adalah membedah naskah iklan (voice-over script) berikut menjadi segmen-segmen adegan visual yang berdurasi ideal sekitar {target_duration} detik per adegan (atau disesuaikan dengan jeda kalimat alami).

Untuk setiap segmen naskah, tentukan:
1. segment_index: integer urut mulai dari 1
2. duration: perkiraan durasi baca narasi dalam detik (sekitar 3.5 - 6 detik)
3. narration_text: potongan teks narasi untuk segmen ini
4. topic: topik adegan (contoh: 'Panggilan Ka'bah', 'Tangis Haru Thawaf', 'Fasilitas Hotel & Kenyamanan', 'Bimbingan Muthawif', 'Ajakan Mendaftar')
5. visual_requirement: deskripsi adegan visual ideal yang dicari editor footage untuk mengisi kalimat narasi ini
6. recommended_mood: mood emosional yang diharapkan (contoh: 'khusyuk', 'haru', 'syahdu', 'megah', 'tenang', 'ceria', 'semangat')

Format output HANYA JSON array dari object segmen:
[
  {{
    "segment_index": 1,
    "duration": 4.5,
    "narration_text": "...",
    "topic": "...",
    "visual_requirement": "...",
    "recommended_mood": "..."
  }}
]

Naskah Iklan:
\"\"\"{script_text}\"\"\"
"""

CANDIDATE_MODELS = [
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.5-flash"
]

class AdsScriptMatcherService:
    @classmethod
    async def analyze_and_match(cls, request: AdsScriptAnalysisRequest) -> AdsScriptAnalysisResponse:
        api_key = get_setting("gemini_api_key") or settings.GEMINI_API_KEY
        segments_raw = []

        if api_key:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=api_key)
                prompt = BREAKDOWN_PROMPT.format(
                    target_duration=request.target_duration_per_scene,
                    script_text=request.script_text
                )
                
                response = None
                for model_name in CANDIDATE_MODELS:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json"
                            )
                        )
                        break
                    except Exception as me:
                        logger.warning(f"Script breakdown failed on {model_name}: {me}")
                
                if not response:
                    raise Exception("All candidate models failed.")

                json_text = response.text.strip()
                if json_text.startswith("```json"):
                    json_text = json_text[7:-3].strip()
                elif json_text.startswith("```"):
                    json_text = json_text[3:-3].strip()

                segments_raw = json.loads(json_text)
            except Exception as e:
                logger.error(f"Error calling Gemini for script breakdown: {e}")
                segments_raw = cls._fallback_segment_splitter(request.script_text, request.target_duration_per_scene)
        else:
            segments_raw = cls._fallback_segment_splitter(request.script_text, request.target_duration_per_scene)

        # Calculate timestamps and match scenes
        total_time = 0.0
        final_segments: List[ScriptSegment] = []

        for seg in segments_raw:
            dur = float(seg.get("duration", request.target_duration_per_scene))
            start_t = round(total_time, 1)
            end_t = round(total_time + dur, 1)
            total_time += dur

            narration = seg.get("narration_text", "")
            topic = seg.get("topic", "Scene Iklan")
            visual_req = seg.get("visual_requirement", narration)
            rec_mood = seg.get("recommended_mood", request.preferred_mood or "khusyuk")

            # Search matching footage scenes
            query_str = f"{topic} {visual_req} {narration}"
            matched_candidates = SceneVectorIndex.search_similar_scenes(
                query_text=query_str,
                top_k=3,
                preferred_mood=rec_mood,
                api_key=api_key
            )

            matched_list = []
            for c in matched_candidates:
                matched_list.append(MatchedScene(
                    file_id=c["file_id"],
                    file_name=c["file_name"],
                    storage_url=c["storage_url"],
                    start_time=c["start_time"],
                    end_time=c["end_time"],
                    location=c.get("location", ""),
                    visual_description=c.get("visual_description", ""),
                    tags=c.get("tags", []),
                    mood=c.get("mood", ""),
                    pacing=c.get("pacing", ""),
                    suitability=c.get("suitability", []),
                    relevance_score=c.get("relevance_score", 85.0),
                    reason=f"Cocok dengan topik '{topic}' dan nuansa visual '{rec_mood}'"
                ))

            final_segments.append(ScriptSegment(
                segment_index=seg.get("segment_index", len(final_segments) + 1),
                estimated_start=start_t,
                estimated_end=end_t,
                duration=dur,
                narration_text=narration,
                topic=topic,
                visual_requirement=visual_req,
                recommended_mood=rec_mood,
                matched_scenes=matched_list
            ))

        return AdsScriptAnalysisResponse(
            total_estimated_duration=round(total_time, 1),
            segments=final_segments,
            summary=f"Naskah berhasil dipecah menjadi {len(final_segments)} segmen visual (~{round(total_time, 1)} detik total durasi) dengan rekomendasi footage relevan."
        )

    @classmethod
    def _fallback_segment_splitter(cls, script_text: str, target_duration: float) -> List[Dict[str, Any]]:
        """Splits sentences cleanly when Gemini API is not yet invoked."""
        import re
        raw_sentences = [s.strip() for s in re.split(r'[.!?\n]+', script_text) if s.strip()]
        if not raw_sentences:
            raw_sentences = [script_text]

        segments = []
        for idx, sentence in enumerate(raw_sentences):
            # approximate 3 words per second
            word_count = len(sentence.split())
            est_duration = max(3.5, min(8.0, round(word_count / 2.8, 1)))

            # infer topic & mood
            s_lower = sentence.lower()
            if any(k in s_lower for k in ["kabah", "ka'bah", "tawaf", "mataf", "hajar"]):
                topic = "Momen Ibadah di Ka'bah"
                mood = "khusyuk"
                req = "Close-up atau wide tawaf jamaah mengelilingi Ka'bah"
            elif any(k in s_lower for k in ["haru", "tangis", "rindu", "air mata", "doa"]):
                topic = "Perasaan Haru & Khusyuk"
                mood = "haru"
                req = "Wajah jamaah berdoa atau tangan menengadah penuh penghayatan"
            elif any(k in s_lower for k in ["nabawi", "madinah", "raudhah", "payung"]):
                topic = "Kesejukan Kota Madinah"
                mood = "syahdu"
                req = "Pemandangan payung Masjid Nabawi atau jamaah berjalan ke Raudhah"
            elif any(k in s_lower for k in ["hotel", "bintang", "fasilitas", "pesawat", "bus", "nyaman"]):
                topic = "Fasilitas & Layanan Unggulan"
                mood = "megah"
                req = "Kemegahan hotel, kenyamanan kamar dan layanan muthawif"
            elif any(k in s_lower for k in ["daftar", "sekarang", "hubungi", "wujudkan", "bersama"]):
                topic = "Ajakan Pendaftaran (Call to Action)"
                mood = "ceria"
                req = "Senyum bahagia para jamaah umrah bersama keluarga"
            else:
                topic = f"Adegan Iklan #{idx+1}"
                mood = "khusyuk"
                req = "Visual suasana ibadah umrah yang relevan"

            segments.append({
                "segment_index": idx + 1,
                "duration": est_duration,
                "narration_text": sentence,
                "topic": topic,
                "visual_requirement": req,
                "recommended_mood": mood
            })
        return segments
