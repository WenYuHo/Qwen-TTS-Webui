from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
import uuid
import random
from pathlib import Path
import json
import logging
from .schemas import SpeakerProfile, MixRequest, VoiceLibrary
from ..config import VOICE_LIBRARY_FILE, logger
from .. import server_state
from ..utils import numpy_to_wav_bytes

router = APIRouter(prefix="/api/voice", tags=["voices"])

# Phonetically-diverse preview sentences — crafted to exercise a wide range
# of vowels, consonants, pauses, emotions, and speech patterns.
PREVIEW_TEXTS = [
    "The quick brown fox jumps gracefully over the lazy dog, enjoying every single moment of freedom.",
    "Yesterday's weather was absolutely perfect — warm sunshine, cool breezes, and a beautiful golden sunset over the mountains.",
    "She whispered softly, 'Don't worry, everything will be alright,' then smiled with quiet confidence.",
    "From quantum physics to classical music, the breadth of human knowledge never ceases to amaze me.",
    "Good morning everyone! Welcome to today's briefing. Let's dive right into the key highlights and explore what's ahead.",
    "The old lighthouse keeper watched as enormous waves crashed against the jagged rocks below, each one thundering louder than the last.",
    "Technology continues to reshape our world in extraordinary ways, connecting billions of people across every continent.",
    "Can you believe how far we've come? Just twenty years ago, none of this would have seemed remotely possible.",
]

PRESETS = [
    {"id": "aiden", "name": "Aiden", "gender": "Male", "description": "Calm, narrative"},
    {"id": "dylan", "name": "Dylan", "gender": "Male", "description": "Young, energetic"},
    {"id": "eric", "name": "Eric", "gender": "Male", "description": "Deep, authoritative"},
    {"id": "ono_anna", "name": "Anna", "gender": "Female", "description": "Soft, clear"},
    {"id": "ryan", "name": "Ryan", "gender": "Male", "description": "Casual, conversational"},
    {"id": "serena", "name": "Serena", "gender": "Female", "description": "Professional, news"},
    {"id": "sohee", "name": "Sohee", "gender": "Female", "description": "Bright, friendly"},
    {"id": "uncle_fu", "name": "Uncle Fu", "gender": "Male", "description": "Older, storytelling"},
    {"id": "vivian", "name": "Vivian", "gender": "Female", "description": "Warm, engaging"}
]

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
        logger.error(f"Voice mix validation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Voice mix validation failed")

@router.post("/preview")
async def voice_preview(request: SpeakerProfile):
    try:
        profile = {"type": request.type, "value": request.value}

        # Use custom text or pick from the curated pool
        text = request.preview_text if request.preview_text else random.choice(PREVIEW_TEXTS)

        # If ref_text is provided (for clone mode), pass it to enable ICL mode
        if request.ref_text:
            profile["ref_text"] = request.ref_text

        # Add clarity instruct hint for better sounding previews
        instruct = "clear speech, natural delivery, steady pace"

        wav, sr = server_state.engine.generate_segment(text, profile=profile, instruct=instruct)

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
        logger.error(f"Failed to load voice library: {e}", exc_info=True)
        return {"voices": []}

@router.post("/library")
async def save_library(library: VoiceLibrary):
    VOICE_LIBRARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(VOICE_LIBRARY_FILE, "w", encoding="utf-8") as f:
            f.write(library.model_dump_json())
        return {"status": "saved"}
    except Exception as e:
        logger.error(f"Failed to save voice library: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save voice library")
