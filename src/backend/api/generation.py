from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from .. import server_state
from ..utils import numpy_to_wav_bytes
from ..dub_logic import run_dub_task
from ..s2s_logic import run_s2s_task, run_batch_s2s_task
from ..utils.subtitles import generate_srt_from_segments, generate_vtt_from_segments
from .schemas import PodcastRequest, S2SRequest, BatchS2SRequest, DubRequest, DiarizeRequest, StreamingSynthesisRequest, DetectLanguageRequest, TEMPERATURE_PRESETS
from ..config import logger
import io

try:
    from ..diarization import diarize_audio
except ImportError:
    diarize_audio = None

router = APIRouter(prefix="/api/generate", tags=["generation"])

import re

EMOTION_MAPPING = {
    "happy": "speak in a cheerful and energetic tone",
    "sad": "speak in a sorrowful and somber tone",
    "angry": "speak in an angry and forceful tone",
    "fear": "speak in a fearful and trembling tone",
    "surprise": "speak in a surprised and excited tone",
    "serious": "speak in a serious and authoritative tone",
    "whispering": "speak in a very soft whispering voice",
    "shouting": "speak in a very loud shouting voice",
}

def parse_script_with_emotions(script_text: str):
    """
    Parses a script string with [Speaker] and [emotion] tags into structured blocks.
    Example:
    [Alice]
    [happy] Hello everyone!
    """
    blocks = []
    current_role = "Default"
    
    # Split by speaker tags: [Name] at the start of a line or after double newline
    # Using a simple line-by-line parser for robustness
    lines = script_text.strip().split("\n")
    
    current_block_text = []
    current_emotion = None
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check for [Speaker] tag
        speaker_match = re.match(r"^\[([^\]]+)\]$", line)
        if speaker_match:
            # If we have accumulated text, save it before switching speaker
            if current_block_text:
                blocks.append({
                    "role": current_role,
                    "text": " ".join(current_block_text),
                    "instruct": EMOTION_MAPPING.get(current_emotion) if current_emotion else None
                })
                current_block_text = []
            
            current_role = speaker_match.group(1)
            current_emotion = None # Reset emotion on speaker change
            continue
            
        # Check for [emotion] tag at the start of a line
        emotion_match = re.match(r"^\[([^\]]+)\]\s*(.*)", line)
        if emotion_match:
            tag = emotion_match.group(1).lower()
            if tag in EMOTION_MAPPING:
                # If we have text with a DIFFERENT emotion, save it
                if current_block_text:
                    blocks.append({
                        "role": current_role,
                        "text": " ".join(current_block_text),
                        "instruct": EMOTION_MAPPING.get(current_emotion) if current_emotion else None
                    })
                    current_block_text = []
                
                current_emotion = tag
                remaining_text = emotion_match.group(2)
                if remaining_text:
                    current_block_text.append(remaining_text)
                continue
        
        # Regular text line
        current_block_text.append(line)
        
    # Add the final block
    if current_block_text:
        blocks.append({
            "role": current_role,
            "text": " ".join(current_block_text),
            "instruct": EMOTION_MAPPING.get(current_emotion) if current_emotion else None
        })
        
    return blocks

@router.post("/parse-script")
async def parse_script_endpoint(request: Dict[str, str]):
    """
    Parses raw script text into structured segments with emotional instructors.
    """
    text = request.get("text", "")
    if not text:
        return {"segments": []}
    
    segments = parse_script_with_emotions(text)
    return {"segments": segments}

@router.post("/stream")
async def stream_synthesis(request: StreamingSynthesisRequest):
    """
    Stream audio chunks for low-latency preview.
    """
    try:
        def audio_generator():
            # Minimal WAV header for the stream might be needed depending on the client
            # but for simplicity we yield raw WAV bytes from each chunk.
            for wav, sr in server_state.engine.stream_synthesize(
                text=request.text,
                profile=request.profile,
                language=request.language or "auto",
                temperature=request.temperature
            ):
                yield numpy_to_wav_bytes(wav, sr).read()

        return StreamingResponse(audio_generator(), media_type="audio/wav")
    except Exception as e:
        logger.error(f"Streaming synthesis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Streaming synthesis failed")

def run_synthesis_task(task_id: str, is_podcast: bool, request_data: PodcastRequest):
    try:
        server_state.task_manager.update_task(task_id, status=server_state.TaskStatus.PROCESSING, progress=10, message="Initializing engine")
        
        # ⚡ Bolt Fix: Handle both dict and Pydantic models correctly
        profiles_map = {}
        if isinstance(request_data.profiles, dict):
            for k, v in request_data.profiles.items():
                # If v is already a dict, use it, else use model_dump
                profiles_map[k] = v if isinstance(v, dict) else v.model_dump()
        else:
            # Fallback for list-based if still exists in some requests
            for p in request_data.profiles:
                p_dict = p if isinstance(p, dict) else p.model_dump()
                profiles_map[p_dict["role"]] = p_dict

        server_state.task_manager.update_task(task_id, progress=30, message="Loading models and starting inference")

        # ⚡ Bolt: Resolve temperature kwargs from preset
        temp_kwargs = dict(TEMPERATURE_PRESETS.get(request_data.temperature_preset or "balanced", TEMPERATURE_PRESETS["balanced"]))
        global_temp = temp_kwargs.pop("temperature", 0.9)
        if request_data.temperature is not None:
            global_temp = request_data.temperature

        if is_podcast:
            script_data = [line.model_dump() for line in request_data.script]
            result = server_state.engine.generate_podcast(
                script_data, 
                profiles=profiles_map, 
                bgm_mood=request_data.bgm_mood, 
                ducking_level=request_data.ducking_level or 0.0,
                eq_preset=request_data.eq_preset or "flat",
                reverb_level=request_data.reverb_level or 0.0,
                master_acx=request_data.master_acx or False,
                temperature=global_temp,
                **temp_kwargs
            )
        else:
            line = request_data.script[0]
            profile = profiles_map.get(line.role)
            wav, sr = server_state.engine.generate_segment(line.text, profile=profile, language=line.language, temperature=line.temperature or global_temp, **temp_kwargs)
            result = {"waveform": wav, "sample_rate": sr}

        server_state.task_manager.update_task(task_id, progress=80, message="Encoding audio")
        if not result:
            raise Exception("Generation returned no audio")

        wav_bytes = numpy_to_wav_bytes(result["waveform"], result["sample_rate"]).read()
        
        result_data = {
            "audio": wav_bytes,
            "segments": result.get("segments", [])
        }
        
        server_state.task_manager.update_task(task_id, status=server_state.TaskStatus.COMPLETED, progress=100, message="Ready", result=result_data)

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        server_state.task_manager.update_task(task_id, status=server_state.TaskStatus.FAILED, error=str(e), message=f"Synthesis failed: {e}")

def run_voice_changer_task(task_id: str, source_audio: str, target_profile: dict):
    try:
        server_state.task_manager.update_task(task_id, status=server_state.TaskStatus.PROCESSING, progress=20, message="Processing source audio...")
        result = server_state.engine.generate_voice_changer(source_audio, target_profile)

        server_state.task_manager.update_task(task_id, progress=80, message="Encoding audio...")
        wav_bytes = numpy_to_wav_bytes(result["waveform"], result["sample_rate"]).read()
        server_state.task_manager.update_task(task_id, status=server_state.TaskStatus.COMPLETED, progress=100, message="Ready", result=wav_bytes)
    except Exception as e:
        logger.error(f"Voice Changer Task {task_id} failed: {e}")
        server_state.task_manager.update_task(task_id, status=server_state.TaskStatus.FAILED, error=str(e), message=f"Voice changer failed: {e}")

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
    try:
        validate_request(request)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    task_id = server_state.task_manager.create_task("segment_generation", {"role": request.script[0].role})
    background_tasks.add_task(run_synthesis_task, task_id, False, request)
    return {"task_id": task_id, "status": server_state.TaskStatus.PENDING}

@router.post("/podcast")
async def generate_podcast(request: PodcastRequest, background_tasks: BackgroundTasks):
    try:
        validate_request(request)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if request.stream:
        try:
            # profiles is now a Dict[str, VoiceProfile]
            if isinstance(request.profiles, dict):
                profiles_map = request.profiles
            else:
                profiles_map = {p["role"]: {"type": p["type"], "value": p["value"]} for p in request.profiles}
            
            def audio_stream():
                for wav, sr, item in server_state.engine.stream_podcast(
                    script=[line.model_dump() for line in request.script],
                    profiles=profiles_map,
                    eq_preset=request.eq_preset or "flat",
                    reverb_level=request.reverb_level or 0.0,
                    temperature=request.temperature
                ):
                    yield numpy_to_wav_bytes(wav, sr).read()
            
            return StreamingResponse(audio_stream(), media_type="audio/wav")
        except Exception as e:
            logger.error(f"Streaming podcast failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Streaming podcast failed")

    task_id = server_state.task_manager.create_task("podcast_generation", {"segments": len(request.script)})
    background_tasks.add_task(run_synthesis_task, task_id, True, request)
    return {"task_id": task_id, "status": server_state.TaskStatus.PENDING}

@router.post("/s2s")
async def generate_s2s(request: S2SRequest, background_tasks: BackgroundTasks):
    if request.stream:
        try:
            def s2s_stream():
                for wav, sr in server_state.engine.stream_voice_changer(
                    source_audio=request.source_audio,
                    target_profile=request.target_voice,
                    preserve_prosody=request.preserve_prosody,
                    instruct=request.instruct
                ):
                    yield numpy_to_wav_bytes(wav, sr).read()
            
            return StreamingResponse(s2s_stream(), media_type="audio/wav")
        except Exception as e:
            logger.error(f"Streaming S2S failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Streaming S2S failed")

    task_id = server_state.task_manager.create_task("s2s", {"source": request.source_audio})
    background_tasks.add_task(run_s2s_task, task_id, request.source_audio, request.target_voice, server_state.engine, request.preserve_prosody, request.instruct)
    return {"task_id": task_id, "status": server_state.TaskStatus.PENDING}

@router.post("/dub")
async def generate_dub(request: DubRequest, background_tasks: BackgroundTasks):
    task_id = server_state.task_manager.create_task("dub", {"source": request.source_audio})
    background_tasks.add_task(run_dub_task, task_id, request.source_audio, request.target_lang, server_state.engine, request.speaker_assignment)
    return {"task_id": task_id, "status": server_state.TaskStatus.PENDING}


@router.post("/detect-language")
async def detect_language(request: DetectLanguageRequest):
    """Detect language from an existing uploaded audio file."""
    try:
        result = server_state.engine.transcribe_audio(request.source_audio)
        return {
            "language": result["language"],
            "text_preview": result["text"][:200]
        }
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/diarize")
async def diarize_audio_endpoint(request: DiarizeRequest):
    """Run speaker diarization on uploaded audio."""
    try:
        if diarize_audio is None:
            raise ImportError("diarization module not available")
            
        # Resolve path
        resolved = server_state.engine._resolve_paths(request.source_audio)
        actual_path = str(resolved[0])
        
        segments = diarize_audio(actual_path, hf_token=request.hf_token)
        
        # Group segments by speaker for easier frontend rendering
        speakers = {}
        for seg in segments:
            speakers.setdefault(seg["speaker"], []).append(seg)
            
        return {
            "speakers": speakers,
            "total_speakers": len(speakers),
            "segments": segments
        }
    except Exception as e:
        logger.error(f"Diarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dub/{task_id}/subtitles")
async def download_subtitles(task_id: str, format: str = "srt"):
    task = server_state.task_manager.get_task(task_id)
    if not task or task["status"] != server_state.TaskStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Task not found or not completed")
    
    result = task.get("result")
    if not isinstance(result, dict) or "segments" not in result:
        raise HTTPException(status_code=400, detail="Subtitles not available for this task")
    
    segments = result["segments"]
    if format == "vtt":
        content = generate_vtt_from_segments(segments)
        return StreamingResponse(io.BytesIO(content.encode()), media_type="text/vtt", headers={"Content-Disposition": f"attachment; filename=subtitles_{task_id}.vtt"})
    else:
        content = generate_srt_from_segments(segments)
        return StreamingResponse(io.BytesIO(content.encode()), media_type="text/plain", headers={"Content-Disposition": f"attachment; filename=subtitles_{task_id}.srt"})

@router.get("/podcast/{task_id}/subtitles")
async def download_podcast_subtitles(task_id: str, format: str = "srt"):
    """Download subtitles for a produced podcast task."""
    task = server_state.task_manager.get_task(task_id)
    if not task or task["status"] != server_state.TaskStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Task not found or not completed")
    
    result = task.get("result")
    if not isinstance(result, dict) or "segments" not in result:
        raise HTTPException(status_code=400, detail="Subtitles not available for this task")
    
    segments = result["segments"]
    if format == "vtt":
        content = generate_vtt_from_segments(segments)
        return StreamingResponse(io.BytesIO(content.encode()), media_type="text/vtt", headers={"Content-Disposition": f"attachment; filename=subtitles_{task_id}.vtt"})
    else:
        content = generate_srt_from_segments(segments)
        return StreamingResponse(io.BytesIO(content.encode()), media_type="text/plain", headers={"Content-Disposition": f"attachment; filename=subtitles_{task_id}.srt"})

@router.get("/dub/{task_id}/lip-sync")
async def download_lip_sync(task_id: str):
    task = server_state.task_manager.get_task(task_id)
    if not task or task["status"] != server_state.TaskStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Task not found or not completed")
    
    result = task.get("result")
    if not isinstance(result, dict) or "mouth_cues" not in result:
        raise HTTPException(status_code=400, detail="Lip-sync data not available for this task")
    
    content = json.dumps({
        "metadata": {"task_id": task_id},
        "mouthCues": result["mouth_cues"]
    }, indent=2)
    
    return StreamingResponse(io.BytesIO(content.encode()), media_type="application/json", headers={"Content-Disposition": f"attachment; filename=lipsync_{task_id}.json"})

@router.post("/s2s/batch")
async def generate_batch_s2s(request: BatchS2SRequest, background_tasks: BackgroundTasks):
    task_id = server_state.task_manager.create_task("batch_s2s", {"count": len(request.source_audios)})
    background_tasks.add_task(run_batch_s2s_task, task_id, request.source_audios, request.target_voice, server_state.engine, request.preserve_prosody, request.instruct)
    return {"task_id": task_id, "status": server_state.TaskStatus.PENDING}
