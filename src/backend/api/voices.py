from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
import uuid
from pathlib import Path
import json
import logging
from .schemas import SpeakerProfile, MixRequest, VoiceLibrary
from ..config import VOICE_LIBRARY_FILE, logger
from .. import server_state
from ..utils import numpy_to_wav_bytes

router = APIRouter(prefix="/api/voice", tags=["voices"])

PRESETS = ["aiden", "dylan", "eric", "ono_anna", "ryan", "serena", "sohee", "uncle_fu", "vivian"]

@router.get("/speakers")
async def get_speakers():
    return {
        "presets": PRESETS,
        "modes": ["preset", "design", "clone", "mix"],
        "languages": ["auto", "en", "zh", "ja", "es"]
    }

@router.post("/upload")
async def upload_voice(file: UploadFile = File(...)):
    upload_dir = server_state.engine.upload_dir

    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in [".wav", ".mp3", ".flac", ".mp4", ".mkv", ".avi", ".mov"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024: # 10MB
        raise HTTPException(status_code=413, detail="File too large")

    safe_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = upload_dir / safe_filename
    with open(file_path, "wb") as f:
        f.write(content)

    return {"filename": safe_filename}

@router.post("/mix")
async def voice_mix(request: MixRequest):
    try:
        for item in request.voices:
            server_state.engine.get_speaker_embedding(item["profile"])
        return {"status": "ok", "message": "Mix configuration validated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preview")
async def voice_preview(request: SpeakerProfile):
    try:
        profile = {"type": request.type, "value": request.value}
        wav, sr = server_state.engine.generate_segment("This is a preview of my voice.", profile=profile)

        # Security: Return audio from memory instead of writing to a public static directory
        # This prevents disk space exhaustion (DoS) and unintended file access.
        buffer = numpy_to_wav_bytes(wav, sr)
        return StreamingResponse(buffer, media_type="audio/wav")
    except Exception as e:
        logger.error(f"Preview failed: {e}", exc_info=True)
        # Security: Return a generic error message instead of leaking internal details
        raise HTTPException(status_code=500, detail="Preview generation failed")

@router.get("/library")
async def get_library():
    if not VOICE_LIBRARY_FILE.exists():
        return {"voices": []}
    try:
        with open(VOICE_LIBRARY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load voice library: {e}")
        return {"voices": []}

@router.post("/library")
async def save_library(library: VoiceLibrary):
    VOICE_LIBRARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(VOICE_LIBRARY_FILE, "w", encoding="utf-8") as f:
            f.write(library.model_dump_json())
        return {"status": "saved"}
    except Exception as e:
        logger.error(f"Failed to save voice library: {e}")
        raise HTTPException(status_code=500, detail=str(e))
