"""Video generation API router — endpoints for LTX-2 video generation."""
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
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
            max_shift=request.max_shift,
            base_shift=request.base_shift,
            terminal=request.terminal,
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
            seed=request.seed,
            max_shift=request.max_shift,
            base_shift=request.base_shift,
            terminal=request.terminal,
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
    Local 'Prompt Architect' utility for LTX-Video.
    This is a rule-based logic to assist users in constructing cinematic prompts.
    Note: This does not use an AI model for suggestion; it is a keyword-based template engine.
    """
    import random
    import re
    
    raw_text = request.text.strip()
    text = raw_text.lower()
    
    # 1. Subject Extraction (Basic)
    # Try to strip common "Role: " prefixes if present
    subject = raw_text
    role_match = re.match(r'^([^\]:]+)(?:\])?\s*:\s*(.*)', raw_text)
    if role_match:
        subject = role_match.group(2).strip()
    
    # Limit subject length for the prompt
    subject = subject[:120]

    # 2. Multi-Layer Cinematic Component Libraries
    atmospheres = {
        "noir": "film noir aesthetic, high contrast, moody, rainy city streets, deep shadows, smoke curling in the air",
        "cyberpunk": "cyberpunk neon-lit environment, high-tech low-life, rainy reflections, flickering holographic advertisements",
        "mystery": "suspenseful, misty atmosphere, dim volumetric lighting, dark cinematic tones, mysterious fog",
        "adventure": "epic adventure mood, vast landscape, heroic lighting, vibrant colors, sweeping vistas",
        "sci-fi": "futuristic sci-fi interior, sterile surfaces, pulsating blue lights, high-tech consoles, metallic sheen",
        "horror": "eerie horror setting, flickering lights, claustrophobic framing, decaying textures, unsettling shadows",
        "nature": "serene natural environment, soft sunlight, lush vegetation, 8k nature photography, peaceful atmosphere",
        "dream": "surreal dreamscape, ethereal light, floating particles, soft focus, otherworldly colors",
        "industrial": "gritty industrial factory, steam vents, rusted metal, warm orange sparks, heavy machinery",
        "vintage": "1970s vintage film aesthetic, warm sepia tones, heavy film grain, nostalgic atmosphere",
        "royal": "opulent royal chamber, gold accents, velvet textures, warm candlelight, majestic lighting"
    }
    
    lightings = [
        "cinematic volumetric lighting", "dramatic Rembrandt lighting", "soft golden hour glow",
        "harsh top-down industrial light", "cool moonlight with deep shadows", "vibrant neon backlighting",
        "natural diffused window light", "flickering candlelight with warm tones", "moody blue-hour lighting",
        "dramatic chiaroscuro lighting"
    ]
    
    shots = [
        "close-up cinematic portrait shot", "wide establishing shot with deep perspective",
        "dynamic low-angle heroic shot", "overhead bird's-eye view", "medium tracking shot, smooth motion",
        "shallow depth of field, bokeh background", "extreme close-up on intricate details",
        "anamorphic widescreen cinematic shot", "dramatic side-profile shot"
    ]
    
    motions = [
        "slow cinematic camera zoom", "steady pan across the scene", "subtle handheld camera shake",
        "dolly-in towards the subject", "static composition with flowing environment elements",
        "dynamic tracking motion", "slow-motion cinematic capture"
    ]

    lenses = [
        "35mm prime lens", "85mm portrait lens", "24mm wide-angle lens", "anamorphic lens", "50mm f/1.8 lens"
    ]

    palettes = [
        "teal and orange color grade", "monochromatic moody tones", "vibrant saturated colors",
        "washed-out vintage colors", "warm earthy color palette", "cool cinematic blue tones"
    ]

    # 3. Architect the suggestion
    # Find matching atmosphere or use default
    atmosphere = "cinematic masterpiece, highly detailed textures"
    for key, val in atmospheres.items():
        if key in text:
            atmosphere = val
            break
            
    lighting = random.choice(lightings)
    shot = random.choice(shots)
    motion = random.choice(motions)
    lens = random.choice(lenses)
    palette = random.choice(palettes)
    
    styles = [
        "photorealistic", "hyper-detailed 8k", "unreal engine 5 render style", 
        "kodak portra 400 aesthetic", "shot on 35mm film", "IMAX cinematic quality"
    ]
    style = random.choice(styles)

    # 4. Construct Final Prompt
    # Structure: [Shot] of [Subject], [Atmosphere], [Lighting], [Motion], [Lens], [Palette], [Style], [Final Polish]
    prompt = (
        f"{shot} of {subject}, {atmosphere}, {lighting}, {motion}, "
        f"{lens}, {palette}, {style}, professional color grading, ultra-high resolution."
    )
    
    return {
        "suggestion": prompt,
        "note": "This suggestion was generated by the local Prompt Architect utility (rule-based)."
    }

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
