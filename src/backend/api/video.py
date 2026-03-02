"""Video generation API router — endpoints for LTX-2 video generation."""
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path

from .. import server_state
from ..config import logger, VIDEO_OUTPUT_DIR
from .schemas import VideoGenerationRequest, NarratedVideoRequest

router = APIRouter(prefix="/api/video", tags=["video"])


def _get_video_engine():
    """Get or lazily create the LTX video engine from server state."""
    if not hasattr(server_state, "video_engine") or server_state.video_engine is None:
        from ..engines.ltx_video_engine import LTXVideoEngine
        server_state.video_engine = LTXVideoEngine()
    return server_state.video_engine


def run_video_generation_task(task_id: str, request: VideoGenerationRequest):
    """Background task for video generation."""
    try:
        engine = _get_video_engine()
        server_state.task_manager.update_task(
            task_id,
            status=server_state.TaskStatus.PROCESSING,
            progress=10,
            message="Loading LTX-2 pipeline...",
        )

        result = engine.generate_video(
            prompt=request.prompt,
            width=request.width,
            height=request.height,
            num_frames=request.num_frames,
            guidance_scale=request.guidance_scale,
            num_inference_steps=request.num_inference_steps,
            seed=request.seed,
        )

        server_state.task_manager.update_task(
            task_id,
            status=server_state.TaskStatus.COMPLETED,
            progress=100,
            message="Video ready",
            result=result,
        )
    except Exception as e:
        logger.error(f"Video generation task {task_id} failed: {e}", exc_info=True)
        server_state.task_manager.update_task(
            task_id,
            status=server_state.TaskStatus.FAILED,
            error=str(e),
            message=f"Video generation failed: {e}",
        )


def _generate_srt(text: str, duration_sec: float) -> str:
    """Simple SRT generator for a single block of text."""
    def format_time(seconds: float) -> str:
        ms = int((seconds % 1) * 1000)
        s = int(seconds % 60)
        m = int((seconds // 60) % 60)
        h = int(seconds // 3600)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    start = format_time(0)
    end = format_time(duration_sec)
    return f"1\n{start} --> {end}\n{text}\n"


def run_narrated_video_task(task_id: str, request: NarratedVideoRequest):
    """Background task for narrated video (TTS + video combined) with subtitle generation."""
    try:
        video_engine = _get_video_engine()
        tts_engine = server_state.engine

        server_state.task_manager.update_task(
            task_id,
            status=server_state.TaskStatus.PROCESSING,
            progress=10,
            message="Generating narration audio...",
        )

        # 1. Generate TTS narration
        profile = request.voice_profile
        wav, sr = tts_engine.generate_segment(
            text=request.narration_text,
            profile=profile,
        )

        duration = len(wav) / sr

        server_state.task_manager.update_task(
            task_id, progress=40, message="Generating video..."
        )

        # 2. Generate narrated video
        result = video_engine.generate_narrated_video(
            prompt=request.prompt,
            narration_wav=wav,
            narration_sr=sr,
            width=request.width,
            height=request.height,
            num_frames=request.num_frames,
            guidance_scale=request.guidance_scale,
            num_inference_steps=request.num_inference_steps,
            seed=request.seed
        )

        # 3. Generate and save SRT
        try:
            video_filename = result.get("video_path")
            if video_filename:
                srt_content = _generate_srt(request.narration_text, duration)
                srt_path = VIDEO_OUTPUT_DIR / f"{Path(video_filename).stem}.srt"
                with open(srt_path, "w", encoding="utf-8") as f:
                    f.write(srt_content)
                result["srt_path"] = srt_path.name
                logger.info(f"Generated subtitles: {srt_path.name}")
        except Exception as srt_err:
            logger.error(f"Failed to generate SRT: {srt_err}")

        server_state.task_manager.update_task(
            task_id,
            status=server_state.TaskStatus.COMPLETED,
            progress=100,
            message="Narrated video ready with subtitles",
            result=result,
        )
    except Exception as e:
        logger.error(f"Narrated video task {task_id} failed: {e}", exc_info=True)
        server_state.task_manager.update_task(
            task_id,
            status=server_state.TaskStatus.FAILED,
            error=str(e),
            message=f"Narrated video generation failed: {e}",
        )


@router.get("/status")
async def video_status():
    """Check if LTX-2 video generation is available."""
    engine = _get_video_engine()
    return engine.get_status()


@router.post("/generate")
async def generate_video(request: VideoGenerationRequest, background_tasks: BackgroundTasks):
    """Generate a video from a text prompt (async)."""
    engine = _get_video_engine()
    if not engine.available:
        return {"error": "LTX-2 video generation is not available. Check model downloads."}

    task_id = server_state.task_manager.create_task(
        "video_generation", {"prompt": request.prompt[:100]}
    )
    background_tasks.add_task(run_video_generation_task, task_id, request)
    return {"task_id": task_id, "status": server_state.TaskStatus.PENDING}


class SuggestionRequest(BaseModel):
    text: str

@router.post("/suggest")
async def suggest_video_scene(request: SuggestionRequest):
    """
    Upgraded 'Prompt Architect' logic for LTX-Video.
    Combines atmosphere, lighting, and camera shots for professional results.
    """
    text = request.text.lower()
    
    # 1. Component Libraries
    atmospheres = {
        "mystery": "suspenseful, misty atmosphere, dark cinematic colors",
        "happy": "vibrant, cheerful mood, warm saturation",
        "sad": "melancholic, somber tone, muted and desaturated",
        "tech": "futuristic high-tech lab, sterile and clean, neon glows",
        "cyberpunk": "gritty cyberpunk aesthetic, rain-slicked surfaces",
        "nature": "lush, organic environment, sun-dappled",
        "dream": "surreal, dreamy quality, soft focus, ethereal"
    }
    
    lightings = {
        "dark": "low-key lighting, deep shadows",
        "bright": "high-key lighting, well-lit",
        "night": "nocturnal lighting, cool moonlight",
        "sunset": "golden hour lighting, long shadows",
        "indoor": "soft volumetric lighting, atmospheric",
        "neon": "colorful neon lighting, dramatic reflections"
    }
    
    shots = {
        "talk": "close-up portrait shot, shallow depth of field",
        "walk": "medium tracking shot, cinematic movement",
        "city": "wide establishing shot, urban skyline",
        "forest": "low-angle ground shot, looking up through leaves",
        "space": "majestic cinematic wide shot, vastness of space"
    }

    # 2. Select Components (with variety)
    import random
    selected_atmosphere = next((v for k, v in atmospheres.items() if k in text), "cinematic, high-detail")
    selected_lighting = next((v for k, v in lightings.items() if k in text), "realistic lighting")
    selected_shot = next((v for k, v in shots.items() if k in text), "cinematic composition")
    
    styles = ["highly detailed", "4k resolution", "masterpiece", "photorealistic", "award-winning cinematography"]
    style_suffix = random.choice(styles)

    # 3. Architect the Prompt
    suggestion = f"A {selected_atmosphere} scene, {selected_shot}, featuring {selected_lighting}, {style_suffix}, high-quality texture, realistic motion."
    
    return {"suggestion": suggestion}

@router.post("/narrated")
async def generate_narrated_video(request: NarratedVideoRequest, background_tasks: BackgroundTasks):
    """Generate a narrated video (TTS audio + LTX-2 video combined)."""
    engine = _get_video_engine()
    if not engine.available:
        return {"error": "LTX-2 video generation is not available. Check model downloads."}

    task_id = server_state.task_manager.create_task(
        "narrated_video", {"prompt": request.prompt[:100]}
    )
    background_tasks.add_task(run_narrated_video_task, task_id, request)
    return {"task_id": task_id, "status": server_state.TaskStatus.PENDING}


@router.get("/{filename}")
async def serve_video(filename: str):
    """Serve a generated video file."""
    # Security: only serve from VIDEO_OUTPUT_DIR, block path traversal
    safe_name = Path(filename).name
    video_path = VIDEO_OUTPUT_DIR / safe_name

    if not video_path.exists():
        return {"error": "Video not found"}

    return FileResponse(str(video_path), media_type="video/mp4", filename=safe_name)
