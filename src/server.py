from fastapi import FastAPI, HTTPException, UploadFile, File
import uuid
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import io
import soundfile as sf
import uvicorn
import sys
from pathlib import Path

# Fix import path for backend modules
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from backend.podcast_engine import PodcastEngine
from backend.config import MODELS

app = FastAPI()

# serve static files
static_dir = current_dir.parent / "static" # src/static
if not static_dir.exists():
    static_dir.mkdir(parents=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Helper to save/stream audio
def numpy_to_wav_bytes(waveform, sample_rate):
    buffer = io.BytesIO()
    sf.write(buffer, waveform, sample_rate, format='WAV')
    buffer.seek(0)
    return buffer

# --- Models ---
class SpeakerProfile(BaseModel):
    role: str
    type: str  # "preset", "design", "clone"
    value: str # "Ryan", "Description", or "filename"

class ScriptLine(BaseModel):
    role: str
    text: str

class PodcastRequest(BaseModel):
    profiles: List[SpeakerProfile]
    script: List[ScriptLine]
    bgm_mood: Optional[str] = None

# --- Engine ---
engine = PodcastEngine()

@app.get("/")
async def read_root():
    return FileResponse(static_dir / "index.html")

@app.get("/api/speakers")
async def get_speakers():
    """Return available preset speakers"""
    return {
        "presets": ["Ryan", "Aiden", "Serena", "Anna", "Tess", "Ono_anna", "Melt", "Yuzu"],
        "modes": ["preset", "design", "clone"]
    }

@app.post("/api/voice/upload")
async def upload_voice(file: UploadFile = File(...)):
    """Handle 3s audio upload for cloning"""
    upload_dir = current_dir.parent / "uploads"
    if not upload_dir.exists():
        upload_dir.mkdir(parents=True)
    
    file_extension = Path(file.filename).suffix
    if file_extension not in [".wav", ".mp3", ".flac"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only WAV, MP3, FLAC supported.")
        
    safe_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = upload_dir / safe_filename
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    return {"filename": str(file_path)}

@app.post("/api/generate/segment")
async def generate_segment(request: PodcastRequest):
    """Generate audio for a single script line (for preview)"""
    if not request.script:
        raise HTTPException(status_code=400, detail="Script is empty")
    
    if len(request.script) > 100:
        raise HTTPException(status_code=400, detail="Script too long (max 100 segments)")
        
    line = request.script[0]
    # Setup profiles (only the one needed for this role)
    for p in request.profiles:
        if p.role == line.role:
            engine.set_speaker_profile(p.role, {"type": p.type, "value": p.value})
            
    try:
        wav, sr = engine.generate_segment(line.role, line.text)
        wav_bytes = numpy_to_wav_bytes(wav, sr)
        return StreamingResponse(wav_bytes, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/podcast")
async def generate_podcast(request: PodcastRequest):
    """
    Generate a podcast from a script.
    """
    print(f"Received request with {len(request.script)} lines, BGM: {request.bgm_mood}")
    
    # 1. Setup profiles
    for p in request.profiles:
        engine.set_speaker_profile(p.role, {"type": p.type, "value": p.value})
        
    # 2. Convert script format
    script_data = [{"role": line.role, "text": line.text} for line in request.script]
    
    # 3. Generate
    try:
        result = engine.generate_podcast(script_data, bgm_mood=request.bgm_mood)
        if not result:
            raise HTTPException(status_code=500, detail="Generation returned no audio")
            
        # 4. Stream back
        wav_bytes = numpy_to_wav_bytes(result["waveform"], result["sample_rate"])
        return StreamingResponse(wav_bytes, media_type="audio/wav")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
