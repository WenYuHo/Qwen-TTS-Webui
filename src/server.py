from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
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
from backend.config import MODELS, logger
from backend.task_manager import task_manager, TaskStatus
from fastapi import BackgroundTasks

app = FastAPI()

# CORS: restrict to localhost origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB
MAX_TEXT_LENGTH = 5000  # per segment
MAX_SCRIPT_SEGMENTS = 100

# serve static files
static_dir = current_dir / "static" # src/static
if not static_dir.exists():
    static_dir.mkdir(parents=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# previews directory
preview_dir = static_dir / "previews"
if not preview_dir.exists():
    preview_dir.mkdir(parents=True)

@app.get("/")
async def read_index():
    return FileResponse(static_dir / "index.html")

@app.get("/favicon.ico")
async def favicon():
    from fastapi import Response
    return Response(status_code=204)

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
    start_time: Optional[float] = None

class PodcastRequest(BaseModel):
    profiles: List[SpeakerProfile]
    script: List[ScriptLine]
    bgm_mood: Optional[str] = None

# --- Engine ---
engine = PodcastEngine()

@app.get("/api/health")
async def health_check():
    """Detailed system and model diagnostics"""
    return engine.get_system_status()

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Check the status of a background task"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Don't return the raw audio bytes in status check to keep response small
    # They will be retrieved via a separate result endpoint or the original task completion logic
    response = task.copy()
    if response["result"] and isinstance(response["result"], bytes):
        response["has_result"] = True
        del response["result"]
    else:
        response["has_result"] = False
        
    return response

@app.get("/api/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """Retrieve the audio result of a completed task"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task not completed yet")
    
    if not task["result"]:
        raise HTTPException(status_code=404, detail="No result found for this task")
    
    return StreamingResponse(io.BytesIO(task["result"]), media_type="audio/wav")

def run_synthesis_task(task_id: str, is_podcast: bool, request_data: PodcastRequest):
    """Background worker for synthesis tasks"""
    try:
        task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=10, message="Initializing engine")
        
        # 1. Setup profiles
        for p in request_data.profiles:
            engine.set_speaker_profile(p.role, {"type": p.type, "value": p.value})
        
        task_manager.update_task(task_id, progress=30, message="Loading models and starting inference")
        
        if is_podcast:
            script_data = [{"role": line.role, "text": line.text, "start_time": line.start_time} for line in request_data.script]
            result = engine.generate_podcast(script_data, bgm_mood=request_data.bgm_mood)
        else:
            line = request_data.script[0]
            wav, sr = engine.generate_segment(line.role, line.text)
            result = {"waveform": wav, "sample_rate": sr}
            
        task_manager.update_task(task_id, progress=80, message="Encoding audio")
        
        if not result:
            raise Exception("Generation returned no audio")
            
        wav_bytes = numpy_to_wav_bytes(result["waveform"], result["sample_rate"]).read()
        
        task_manager.update_task(task_id, status=TaskStatus.COMPLETED, progress=100, message="Ready", result=wav_bytes)
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        task_manager.update_task(task_id, status=TaskStatus.FAILED, error=str(e), message="Synthesis failed")

@app.get("/api/speakers")
async def get_speakers():
    """Return available preset speakers"""
    return {
        "presets": ["aiden", "dylan", "eric", "ono_anna", "ryan", "serena", "sohee", "uncle_fu", "vivian"],
        "modes": ["preset", "design", "clone"]
    }

@app.post("/api/voice/upload")
async def upload_voice(file: UploadFile = File(...)):
    """Handle 3s audio upload for cloning"""
    upload_dir = current_dir.parent / "uploads"
    if not upload_dir.exists():
        upload_dir.mkdir(parents=True)
    
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in [".wav", ".mp3", ".flac"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only WAV, MP3, FLAC supported.")

    # Read with size limit
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024*1024)}MB.")
        
    safe_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = upload_dir / safe_filename
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Return only the filename, not the full server path
    return {"filename": str(file_path)}

@app.post("/api/generate/segment")
async def generate_segment(request: PodcastRequest, background_tasks: BackgroundTasks):
    """Start async generation for a single script line"""
    if not request.script:
        raise HTTPException(status_code=400, detail="Script is empty")
    
    if len(request.script) > MAX_SCRIPT_SEGMENTS:
        raise HTTPException(status_code=400, detail=f"Script too long (max {MAX_SCRIPT_SEGMENTS} segments)")

    # Validate text lengths
    for line in request.script:
        if len(line.text) > MAX_TEXT_LENGTH:
            raise HTTPException(status_code=400, detail=f"Text too long for role '{line.role}' (max {MAX_TEXT_LENGTH} chars)")
        
    task_id = task_manager.create_task("segment_generation", {"role": request.script[0].role})
    background_tasks.add_task(run_synthesis_task, task_id, False, request)
    
    return {"task_id": task_id, "status": TaskStatus.PENDING}

@app.post("/api/generate/podcast")
async def generate_podcast(request: PodcastRequest, background_tasks: BackgroundTasks):
    """
    Start async podcast generation.
    """
    if not request.script:
        raise HTTPException(status_code=400, detail="Script is empty")
    
    if len(request.script) > MAX_SCRIPT_SEGMENTS:
        raise HTTPException(status_code=400, detail=f"Script too long (max {MAX_SCRIPT_SEGMENTS} segments)")

    # Validate text lengths
    for line in request.script:
        if len(line.text) > MAX_TEXT_LENGTH:
            raise HTTPException(status_code=400, detail=f"Text too long for role '{line.role}' (max {MAX_TEXT_LENGTH} chars)")

    print(f"Received request with {len(request.script)} lines, BGM: {request.bgm_mood}")
    
    task_id = task_manager.create_task("podcast_generation", {"segments": len(request.script)})
    background_tasks.add_task(run_synthesis_task, task_id, True, request)
    
    return {"task_id": task_id, "status": TaskStatus.PENDING}

@app.post("/api/voice/preview")
async def voice_preview(request: SpeakerProfile):
    """Generate and cache a preview for a specific voice"""
    # Use role or name as part of filename handle
    # Clean role name for filename
    safe_name = "".join([c for c in request.role if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
    preview_path = preview_dir / f"{safe_name}.wav"
    
    # If exists, return cached
    if preview_path.exists():
        return FileResponse(preview_path)
        
    # Generate new
    try:
        engine.set_speaker_profile(request.role, {"type": request.type, "value": request.value})
        test_text = "This is a preview of my voice."
        wav, sr = engine.generate_segment(request.role, test_text)
        
        # Save to file
        sf.write(str(preview_path), wav, sr, format='WAV')
        
        return FileResponse(preview_path)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

# --- Project Management (Phase 1) ---

PROJECTS_DIR = current_dir.parent / "projects"
if not PROJECTS_DIR.exists():
    PROJECTS_DIR.mkdir(parents=True)

class ProjectBlock(BaseModel):
    id: str
    role: str
    text: str
    status: str
    # Future: start_time, duration, track_id

class ProjectData(BaseModel):
    name: str # Project name
    blocks: List[ProjectBlock]
    script_draft: Optional[str] = ""

@app.get("/api/projects")
async def list_projects():
    """List all saved projects"""
    projects = []
    for f in PROJECTS_DIR.glob("*.json"):
        projects.append(f.stem)
    return {"projects": projects}

@app.post("/api/projects/{name}")
async def save_project(name: str, data: ProjectData):
    """Save a project to disk"""
    safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
    if not safe_name:
        raise HTTPException(status_code=400, detail="Invalid project name")
        
    file_path = PROJECTS_DIR / f"{safe_name}.json"
    import json
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(data.json())
        
    return {"status": "saved", "name": safe_name}

@app.get("/api/projects/{name}")
async def load_project(name: str):
    """Load a project from disk"""
    file_path = PROJECTS_DIR / f"{name}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
        
    return FileResponse(file_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
