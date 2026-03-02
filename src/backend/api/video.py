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


def run_narrated_video_task(task_id: str, request: NarratedVideoRequest):
    """Background task for narrated video (TTS + video combined)."""
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
        )

        server_state.task_manager.update_task(
            task_id,
            status=server_state.TaskStatus.COMPLETED,
            progress=100,
            message="Narrated video ready",
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
