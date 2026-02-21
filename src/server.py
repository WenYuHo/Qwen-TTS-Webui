from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import io
import soundfile as sf
import uvicorn
import sys
import uuid
import json
from pathlib import Path

# Fix import path for backend modules
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from backend.podcast_engine import PodcastEngine
from backend.config import MODELS, logger
from backend.task_manager import task_manager, TaskStatus
from backend.s2s_logic import run_s2s_task
from backend.dub_logic import run_dub_task
from backend.utils import numpy_to_wav_bytes

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
static_dir = current_dir / "static"
if not static_dir.exists():
    static_dir.mkdir(parents=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

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

class S2SRequest(BaseModel):
    source_audio: str
    target_voice: dict

class DubRequest(BaseModel):
    source_audio: str
    target_lang: str

class ProjectBlock(BaseModel):
    id: str
    role: str
    text: str
    status: str

class ProjectData(BaseModel):
    name: str
    blocks: List[ProjectBlock]
    script_draft: Optional[str] = ""

# --- Engine ---
engine = PodcastEngine()

@app.get("/api/health")
async def health_check():
    return engine.get_system_status()

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response = task.copy()
    if response["result"] and isinstance(response["result"], bytes):
        response["has_result"] = True
        del response["result"]
    else:
        response["has_result"] = False
        
    return response

@app.get("/api/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task not completed yet")
    
    if not task["result"]:
        raise HTTPException(status_code=404, detail="No result found for this task")
    
    return StreamingResponse(io.BytesIO(task["result"]), media_type="audio/wav")

def run_synthesis_task(task_id: str, is_podcast: bool, request_data: PodcastRequest):
    try:
        task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=10, message="Initializing engine")
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
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        task_manager.update_task(task_id, status=TaskStatus.FAILED, error=str(e), message=f"Synthesis failed: {e}")

@app.get("/api/speakers")
async def get_speakers():
    return {
        "presets": ["aiden", "dylan", "eric", "ono_anna", "ryan", "serena", "sohee", "uncle_fu", "vivian"],
        "modes": ["preset", "design", "clone"]
    }

@app.post("/api/voice/upload")
async def upload_voice(file: UploadFile = File(...)):
    upload_dir = engine.upload_dir
    
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in [".wav", ".mp3", ".flac"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large")

    safe_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = upload_dir / safe_filename
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {"filename": safe_filename}

def validate_request(request: PodcastRequest):
    if not request.script:
        raise HTTPException(status_code=400, detail="Script is empty")
    if len(request.script) > MAX_SCRIPT_SEGMENTS:
        raise HTTPException(status_code=400, detail="Script too long")
    for line in request.script:
        if len(line.text) > MAX_TEXT_LENGTH:
            raise HTTPException(status_code=400, detail="Text too long")

@app.post("/api/generate/segment")
async def generate_segment(request: PodcastRequest, background_tasks: BackgroundTasks):
    validate_request(request)
    task_id = task_manager.create_task("segment_generation", {"role": request.script[0].role})
    background_tasks.add_task(run_synthesis_task, task_id, False, request)
    return {"task_id": task_id, "status": TaskStatus.PENDING}

@app.post("/api/generate/podcast")
async def generate_podcast(request: PodcastRequest, background_tasks: BackgroundTasks):
    validate_request(request)
    task_id = task_manager.create_task("podcast_generation", {"segments": len(request.script)})
    background_tasks.add_task(run_synthesis_task, task_id, True, request)
    return {"task_id": task_id, "status": TaskStatus.PENDING}

@app.post("/api/generate/s2s")
async def generate_s2s(request: S2SRequest, background_tasks: BackgroundTasks):
    task_id = task_manager.create_task("s2s_generation", {"source": request.source_audio})
    background_tasks.add_task(run_s2s_task, task_id, request.source_audio, request.target_voice, engine)
    return {"task_id": task_id, "status": TaskStatus.PENDING}

@app.post("/api/generate/dub")
async def generate_dub(request: DubRequest, background_tasks: BackgroundTasks):
    task_id = task_manager.create_task("dubbing", {"source": request.source_audio})
    background_tasks.add_task(run_dub_task, task_id, request.source_audio, request.target_lang, engine)
    return {"task_id": task_id, "status": TaskStatus.PENDING}

@app.post("/api/voice/preview")
async def voice_preview(request: SpeakerProfile):
    safe_name = "".join([c for c in request.role if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
    preview_path = preview_dir / f"{safe_name}.wav"
    if preview_path.exists():
        return FileResponse(preview_path)
    try:
        engine.set_speaker_profile(request.role, {"type": request.type, "value": request.value})
        wav, sr = engine.generate_segment(request.role, "This is a preview of my voice.")
        sf.write(str(preview_path), wav, sr, format='WAV')
        return FileResponse(preview_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Project Management ---
PROJECTS_DIR = current_dir.parent / "projects"
if not PROJECTS_DIR.exists():
    PROJECTS_DIR.mkdir(parents=True)

@app.get("/api/projects")
async def list_projects():
    return {"projects": [f.stem for f in PROJECTS_DIR.glob("*.json")]}

@app.post("/api/projects/{name}")
async def save_project(name: str, data: ProjectData):
    safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
    file_path = PROJECTS_DIR / f"{safe_name}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(data.model_dump_json())
    return {"status": "saved", "name": safe_name}

@app.get("/api/projects/{name}")
async def load_project(name: str):
    file_path = PROJECTS_DIR / f"{name}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(file_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
