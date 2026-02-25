from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import uuid
from pathlib import Path
import json
import logging
import soundfile as sf
from .schemas import SpeakerProfile, MixRequest, VoiceLibrary
from ..config import VOICE_LIBRARY_FILE, logger

router = APIRouter(prefix="/api/voice", tags=["voices"])

@router.get("/speakers")
async def get_speakers():
    return {
        "presets": ["aiden", "dylan", "eric", "ono_anna", "ryan", "serena", "sohee", "uncle_fu", "vivian"],
        "modes": ["preset", "design", "clone", "mix"],
        "languages": ["auto", "en", "zh", "ja", "es"]
    }

@router.post("/upload")
async def upload_voice(file: UploadFile = File(...)):
    from ..server_state import engine
    upload_dir = engine.upload_dir

    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in [".wav", ".mp3", ".flac"]:
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
    from ..server_state import engine
    try:
        for item in request.voices:
            engine.get_speaker_embedding(item["profile"])
        return {"status": "ok", "message": "Mix configuration validated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preview")
async def voice_preview(request: SpeakerProfile):
    from ..server_state import engine
    preview_dir = Path("src/static/previews")
    preview_dir.mkdir(parents=True, exist_ok=True)

    # Security: Use UUID for preview filename to prevent path traversal and collision
    safe_name = f"preview_{uuid.uuid4().hex[:12]}"
    preview_path = preview_dir / f"{safe_name}.wav"

    try:
        engine.set_speaker_profile(request.role, {"type": request.type, "value": request.value})
        wav, sr = engine.generate_segment(request.role, "This is a preview of my voice.")
        sf.write(str(preview_path), wav, sr, format='WAV')
        return FileResponse(preview_path)
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
