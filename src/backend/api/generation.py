from fastapi import APIRouter, HTTPException, BackgroundTasks
from .. import server_state
from ..utils import numpy_to_wav_bytes
from ..dub_logic import run_dub_task
from ..s2s_logic import run_s2s_task
from .schemas import PodcastRequest, S2SRequest, DubRequest
from ..config import logger
import io

router = APIRouter(prefix="/api/generate", tags=["generation"])

def run_synthesis_task(task_id: str, is_podcast: bool, request_data: PodcastRequest):
    try:
        server_state.task_manager.update_task(task_id, status=server_state.TaskStatus.PROCESSING, progress=10, message="Initializing engine")
        profiles_map = {p["role"]: {"type": p["type"], "value": p["value"]} for p in request_data.profiles}

        server_state.task_manager.update_task(task_id, progress=30, message="Loading models and starting inference")

        if is_podcast:
            script_data = [line.model_dump() for line in request_data.script]
            result = server_state.engine.generate_podcast(script_data, profiles=profiles_map, bgm_mood=request_data.bgm_mood)
        else:
            line = request_data.script[0]
            profile = profiles_map.get(line.role)
            wav, sr = server_state.engine.generate_segment(line.text, profile=profile, language=line.language)
            result = {"waveform": wav, "sample_rate": sr}

        server_state.task_manager.update_task(task_id, progress=80, message="Encoding audio")
        if not result:
            raise Exception("Generation returned no audio")

        wav_bytes = numpy_to_wav_bytes(result["waveform"], result["sample_rate"]).read()
        server_state.task_manager.update_task(task_id, status=server_state.TaskStatus.COMPLETED, progress=100, message="Ready", result=wav_bytes)

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        server_state.task_manager.update_task(task_id, status=server_state.TaskStatus.FAILED, error="Synthesis error", message="Synthesis failed. Please check your inputs or logs.")

def run_voice_changer_task(task_id: str, source_audio: str, target_profile: dict):
    try:
        server_state.task_manager.update_task(task_id, status=server_state.TaskStatus.PROCESSING, progress=20, message="Processing source audio...")
        result = server_state.engine.generate_voice_changer(source_audio, target_profile)

        server_state.task_manager.update_task(task_id, progress=80, message="Encoding audio...")
        wav_bytes = numpy_to_wav_bytes(result["waveform"], result["sample_rate"]).read()
        server_state.task_manager.update_task(task_id, status=server_state.TaskStatus.COMPLETED, progress=100, message="Ready", result=wav_bytes)
    except Exception as e:
        logger.error(f"Voice Changer Task {task_id} failed: {e}", exc_info=True)
        server_state.task_manager.update_task(task_id, status=server_state.TaskStatus.FAILED, error="Voice changer error", message="Voice changer failed. Please check your inputs or logs.")

def validate_request(request: PodcastRequest):
    if not request.script:
        raise HTTPException(status_code=400, detail='Script is empty')
    if len(request.script) > 100:
        raise HTTPException(status_code=400, detail='Script too long')
    for line in request.script:
        if len(line.text) > 5000:
            raise HTTPException(status_code=400, detail='Text too long')

@router.post("/segment")
async def generate_segment(request: PodcastRequest, background_tasks: BackgroundTasks):
    validate_request(request)
    task_id = server_state.task_manager.create_task("segment_generation", {"role": request.script[0].role})
    background_tasks.add_task(run_synthesis_task, task_id, False, request)
    return {"task_id": task_id, "status": server_state.TaskStatus.PENDING}

@router.post("/podcast")
async def generate_podcast(request: PodcastRequest, background_tasks: BackgroundTasks):
    validate_request(request)
    task_id = server_state.task_manager.create_task("podcast_generation", {"segments": len(request.script)})
    background_tasks.add_task(run_synthesis_task, task_id, True, request)
    return {"task_id": task_id, "status": server_state.TaskStatus.PENDING}

@router.post("/s2s")
async def generate_s2s(request: S2SRequest, background_tasks: BackgroundTasks):
    if request.preserve_prosody:
        task_id = server_state.task_manager.create_task("voice_changer", {"source": request.source_audio})
        background_tasks.add_task(run_voice_changer_task, task_id, request.source_audio, request.target_voice)
    else:
        task_id = server_state.task_manager.create_task("s2s_generation", {"source": request.source_audio})
        background_tasks.add_task(run_s2s_task, task_id, request.source_audio, request.target_voice, server_state.engine)
    return {"task_id": task_id, "status": server_state.TaskStatus.PENDING}

@router.post("/dub")
async def generate_dub(request: DubRequest, background_tasks: BackgroundTasks):
    task_id = server_state.task_manager.create_task("dubbing", {"source": request.source_audio})
    background_tasks.add_task(run_dub_task, task_id, request.source_audio, request.target_lang, server_state.engine)
    return {"task_id": task_id, "status": server_state.TaskStatus.PENDING}
