import os
import json
import logging
from typing import Dict, Any, List, Optional
from app.config import settings
from app.database import get_setting
from app.models import SceneMetadata, FileMetadata

logger = logging.getLogger(__name__)

GEMINI_ANALYSIS_PROMPT = """
Anda adalah AI Video & Photo Indexer profesional spesialis footage dokumentasi perjalanan Umrah dan Haji untuk kebutuhan video editor iklan.
Tugas Anda adalah menganalisa media ini secara komprehensif, detik-demi-detik.

Pecah video ini menjadi rangkaian scene visual yang jelas (tiap scene biasanya berdurasi 3-8 detik saat terjadi perubahan sudut kamera, subjek, atau aktivitas).
Untuk setiap scene, berikan informasi berikut dalam format JSON:
- start_time: Waktu mulai scene dalam detik (misal: 0.0)
- end_time: Waktu selesai scene dalam detik (misal: 4.5)
- location: Nama lokasi spesifik (contoh: 'Masjidil Haram - Mataf', 'Masjidil Haram - Pintu King Abdulaziz', 'Masjid Nabawi - Pelataran Payung', 'Jabal Uhud', 'Bus Jamaah', 'Hotel Makkah')
- visual_description: Deskripsi visual mendalam (subjek jamaah, pakaian ihram/seragam, aktivitas ibadah/berdoa/tawaf/sai/ziarah, sudut kamera close-up/wide/medium/aerial)
- tags: List keyword relevan bahasa Indonesia & Inggris (contoh: ['kabah', 'tawaf', 'crowd', 'day', 'wide-shot'])
- mood: Suasana emosional (khusyuk, haru, megah, syahdu, ceria, dinamis, tenang)
- pacing: Tempo pergerakan (slow, medium, fast)
- suitability: Potensi penggunaan di iklan (pilihan: ['opening', 'emotional_hook', 'ibadah', 'broll', 'narration_fasilitas', 'narration_syarat_rukun', 'closing', 'call_to_action'])

Keluarkan HANYA JSON murni dengan format:
{
  "duration_seconds": 30.0,
  "scenes": [
    {
      "start_time": 0.0,
      "end_time": 4.5,
      "location": "...",
      "visual_description": "...",
      "tags": ["..."],
      "mood": "...",
      "pacing": "...",
      "suitability": ["..."]
    }
  ]
}
"""

CANDIDATE_MODELS = [
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.5-flash"
]

class GeminiAnalyzerService:
    @classmethod
    def get_api_key(cls) -> Optional[str]:
        return get_setting("gemini_api_key") or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.get_api_key())

    @classmethod
    async def analyze_media_file(cls, file_path: Optional[str], file_name: str, file_type: str, file_id: str, storage_url: str) -> FileMetadata:
        api_key = cls.get_api_key()
        
        if api_key and file_path and os.path.exists(file_path):
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=api_key)
                logger.info(f"Uploading {file_name} to Gemini File API...")
                
                uploaded_file = client.files.upload(file=file_path)
                
                if file_type == "video":
                    import time
                    while uploaded_file.state.name == "PROCESSING":
                        time.sleep(2)
                        uploaded_file = client.files.get(name=uploaded_file.name)
                    
                    if uploaded_file.state.name == "FAILED":
                        raise Exception("Gemini video processing failed.")

                logger.info(f"Analyzing {file_name} with Gemini Flash...")
                
                response = None
                last_err = None
                for model_name in CANDIDATE_MODELS:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[
                                uploaded_file,
                                GEMINI_ANALYSIS_PROMPT
                            ],
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json"
                            )
                        )
                        logger.info(f"Successfully analyzed with model: {model_name}")
                        break
                    except Exception as me:
                        logger.warning(f"Model {model_name} failed: {me}. Trying next model...")
                        last_err = me

                if not response:
                    raise last_err or Exception("All candidate Gemini models failed.")

                try:
                    client.files.delete(name=uploaded_file.name)
                except Exception as del_err:
                    logger.warning(f"Failed to delete temp file from Gemini: {del_err}")

                json_text = response.text.strip()
                if json_text.startswith("```json"):
                    json_text = json_text[7:-3].strip()
                elif json_text.startswith("```"):
                    json_text = json_text[3:-3].strip()

                parsed = json.loads(json_text)
                duration = parsed.get("duration_seconds", 30.0)
                scenes = [SceneMetadata(**s) for s in parsed.get("scenes", [])]

                return FileMetadata(
                    file_id=file_id,
                    file_name=file_name,
                    file_type=file_type,
                    storage_url=storage_url,
                    duration_seconds=duration,
                    scenes=scenes
                )

            except Exception as e:
                logger.error(f"Error calling Gemini API for {file_name}: {e}")
                return cls._generate_smart_simulation(file_id, file_name, file_type, storage_url)
        else:
            return cls._generate_smart_simulation(file_id, file_name, file_type, storage_url)

    @classmethod
    def _generate_smart_simulation(cls, file_id: str, file_name: str, file_type: str, storage_url: str) -> FileMetadata:
        name_lower = file_name.lower()
        
        if file_type == "image":
            return FileMetadata(
                file_id=file_id,
                file_name=file_name,
                file_type="image",
                storage_url=storage_url,
                duration_seconds=0.0,
                scenes=[
                    SceneMetadata(
                        start_time=0.0,
                        end_time=0.0,
                        location="Makkah - Pelataran Menara Jam",
                        visual_description=f"Foto pemandangan megah menara jam Makkah Royal Clock Tower dari arah pelataran hotel dengan sudut eye-level. ({file_name})",
                        tags=["hotel", "makkah", "clock-tower", "luxury", "landscape"],
                        mood="megah",
                        pacing="slow",
                        suitability=["broll", "narration_fasilitas", "opening"]
                    )
                ]
            )

        if "towaf" in name_lower or "tawaf" in name_lower:
            scenes = [
                SceneMetadata(
                    start_time=0.0,
                    end_time=4.5,
                    location="Masjidil Haram - Mataf",
                    visual_description="Jamaah sedang tawaf mengelilingi Ka'bah, sudut pengambilan wide angle dari lantai 1. Suasana ramai khusyuk di siang hari.",
                    tags=["kabah", "tawaf", "crowd", "day", "wide-shot"],
                    mood="khusyuk",
                    pacing="slow",
                    suitability=["opening", "emotional_hook", "ibadah"]
                ),
                SceneMetadata(
                    start_time=4.5,
                    end_time=9.0,
                    location="Masjidil Haram - Hajar Aswad",
                    visual_description="Close-up tangan jamaah melambai istilam ke arah Hajar Aswad dengan wajah penuh haru.",
                    tags=["istilam", "hajar-aswad", "close-up", "hands", "haru"],
                    mood="haru",
                    pacing="medium",
                    suitability=["broll", "narration_syarat_rukun", "emotional_hook"]
                ),
                SceneMetadata(
                    start_time=9.0,
                    end_time=15.0,
                    location="Masjidil Haram - Maqam Ibrahim",
                    visual_description="Medium shot jamaah salat sunnah di belakang Maqam Ibrahim dengan latar belakang Ka'bah.",
                    tags=["maqam-ibrahim", "sholat", "medium-shot", "doa"],
                    mood="tenang",
                    pacing="slow",
                    suitability=["ibadah", "broll"]
                )
            ]
            duration = 15.0
        elif "nabawi" in name_lower or "payung" in name_lower:
            scenes = [
                SceneMetadata(
                    start_time=0.0,
                    end_time=5.0,
                    location="Masjid Nabawi - Pelataran Payung",
                    visual_description="Pemandangan indah mekarnya payung raksasa di pelataran Masjid Nabawi saat fajar menjelang pagi. Warna langit keemasan.",
                    tags=["payung-nabawi", "madinah", "fajar", "cinematic", "wide-shot"],
                    mood="syahdu",
                    pacing="slow",
                    suitability=["opening", "emotional_hook", "narration_fasilitas"]
                ),
                SceneMetadata(
                    start_time=5.0,
                    end_time=11.0,
                    location="Masjid Nabawi - Pintu Masuk Kubah Hijau",
                    visual_description="Jamaah berjalan santai memasuki area Raudhah dan makam Rasulullah SAW dengan ekspresi bahagia.",
                    tags=["raudhah", "kubah-hijau", "jamaah", "senyum", "ziarah"],
                    mood="haru",
                    pacing="medium",
                    suitability=["narration_syarat_rukun", "closing"]
                )
            ]
            duration = 11.0
        elif "uhud" in name_lower or "ziarah" in name_lower:
            scenes = [
                SceneMetadata(
                    start_time=0.0,
                    end_time=6.0,
                    location="Madinah - Jabal Uhud",
                    visual_description="Landscape pemandangan bukit Jabal Uhud dengan para peziarah mendengarkan tausiyah dari muthawif.",
                    tags=["jabal-uhud", "ziarah", "muthawif", "sejarah", "landscape"],
                    mood="megah",
                    pacing="medium",
                    suitability=["broll", "narration_fasilitas"]
                ),
                SceneMetadata(
                    start_time=6.0,
                    end_time=12.0,
                    location="Makam Syuhada Uhud",
                    visual_description="Jamaah memanjatkan doa bersama di depan area makam Syuhada Uhud dengan penuh perenungan.",
                    tags=["syuhada-uhud", "doa", "ziarah", "khusyuk"],
                    mood="khusyuk",
                    pacing="slow",
                    suitability=["emotional_hook", "narration_syarat_rukun"]
                )
            ]
            duration = 12.0
        else:
            scenes = [
                SceneMetadata(
                    start_time=0.0,
                    end_time=5.0,
                    location="Makkah / Madinah",
                    visual_description=f"Dokumentasi aktivitas jamaah umrah pada footage {file_name}. Suasana hangat dan penuh kebersamaan.",
                    tags=["jamaah", "kebersamaan", "umrah", "perjalanan"],
                    mood="ceria",
                    pacing="medium",
                    suitability=["broll", "closing"]
                ),
                SceneMetadata(
                    start_time=5.0,
                    end_time=10.0,
                    location="Area Ibadah",
                    visual_description="Jamaah saling mendoakan dan tersenyum mengenakan seragam rombongan umrah.",
                    tags=["doa", "senyum", "rombongan", "keluarga"],
                    mood="haru",
                    pacing="slow",
                    suitability=["emotional_hook", "call_to_action"]
                )
            ]
            duration = 10.0

        return FileMetadata(
            file_id=file_id,
            file_name=file_name,
            file_type=file_type,
            storage_url=storage_url,
            duration_seconds=duration,
            scenes=scenes
        )
