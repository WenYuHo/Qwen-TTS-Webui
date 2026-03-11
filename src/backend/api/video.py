"""Video generation API router — endpoints for LTX-2 video generation."""
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import uuid
import numpy as np
import re

from .. import server_state
from ..config import logger, VIDEO_OUTPUT_DIR
from .schemas import VideoGenerationRequest, NarratedVideoRequest, VideoScene

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


def _concat_scenes(scene_clips: list) -> str:
    """Concatenate multiple video clips with transitions and frame-accurate sync."""
    from moviepy import VideoFileClip, concatenate_videoclips, vfx

    clips = []
    try:
        for sc in scene_clips:
            clip_path = str(VIDEO_OUTPUT_DIR / sc["video_path"])
            logger.info(f"Loading clip for concatenation: {clip_path} (Target duration: {sc['duration']:.2f}s)")
            
            clip = VideoFileClip(clip_path)
            
            # ⚡ Sync Enhancement: Ensure video duration matches audio exactly
            # This prevents cumulative drift in long multi-scene videos
            if abs(clip.duration - sc["duration"]) > 0.001:
                logger.info(f"⚡ Sync: Rescaling clip from {clip.duration:.3f}s to {sc['duration']:.3f}s")
                clip = clip.with_effects([vfx.speedx(final_duration=sc["duration"])])

            if sc.get("transition") == "fade":
                clip = clip.with_effects([lambda c: c.fadein(0.5), lambda c: c.fadeout(0.5)])
            elif sc.get("transition") == "dissolve":
                clip = clip.with_effects([lambda c: c.crossfadein(0.5)])
            
            clips.append(clip)

        final = concatenate_videoclips(clips, method="compose")
        output_filename = f"narrated_{uuid.uuid4()}.mp4"
        output_path = VIDEO_OUTPUT_DIR / output_filename
        
        logger.info(f"Writing final concatenated video to {output_path}")
        final.write_videofile(
            str(output_path), 
            codec="libx264", 
            audio_codec="aac", 
            fps=25,
            logger=None
        )

        # Cleanup individual clips
        for clip in clips:
            try:
                clip.close()
            except:
                pass
        
        return output_filename
    except Exception as e:
        logger.error(f"Failed to concatenate scenes: {e}", exc_info=True)
        # Cleanup if possible
        for clip in clips:
            try:
                clip.close()
            except:
                pass
        # Fallback to first clip if concatenation fails
        return scene_clips[0]["video_path"]


def run_narrated_video_task(task_id: str, request: NarratedVideoRequest):
    """Background task for narrated video (TTS + video combined) with multi-scene support."""
    try:
        from ..utils.subtitles import generate_srt, burn_subtitles
        video_engine = _get_video_engine()
        tts_engine = server_state.engine

        # Backward compat: convert legacy single-scene to scenes list
        scenes = request.scenes or [VideoScene(
            video_prompt=request.prompt,
            narration_text=request.narration_text,
            voice_profile=request.voice_profile,
            camera_motion=request.camera_motion
        )]

        total = len(scenes)
        scene_clips = []  # List of dicts with metadata

        for i, scene in enumerate(scenes):
            pct = int(10 + (80 * i / total))
            server_state.task_manager.update_task(
                task_id, 
                progress=pct,
                message=f"Scene {i+1}/{total}: Generating narration..."
            )

            # 1. Generate TTS for this scene
            profile = scene.voice_profile or request.voice_profile
            wav, sr = tts_engine.generate_segment(
                text=scene.narration_text, 
                profile=profile,
                instruct=scene.instruct
            )
            audio_duration = len(wav) / sr

            # 2. Calculate video frames to match audio duration
            num_frames = max(9, int(audio_duration * 25) + 1)

            server_state.task_manager.update_task(
                task_id, 
                progress=pct + 5,
                message=f"Scene {i+1}/{total}: Generating video ({num_frames} frames)..."
            )

            # ⚡ Cinematic Enhancement: Inject camera motion into prompt
            final_prompt = scene.video_prompt
            motion = scene.camera_motion or request.camera_motion
            if motion and motion.strip():
                # Prepend motion keyword to guide the model's lens
                final_prompt = f"{motion.strip()}, {final_prompt}"
                logger.info(f"⚡ Cinematic: Injecting motion '{motion}' into scene {i+1}")

            # 3. Generate video for this scene
            result = video_engine.generate_narrated_video(
                prompt=final_prompt,
                narration_wav=wav,
                narration_sr=sr,
                width=request.width,
                height=request.height,
                num_frames=num_frames,
                guidance_scale=request.guidance_scale,
                num_inference_steps=request.num_inference_steps,
                seed=request.seed,
                max_shift=request.max_shift,
                base_shift=request.base_shift,
                terminal=request.terminal,
            )
            
            scene_clips.append({
                "video_path": result.get("video_path"),
                "duration": audio_duration,
                "transition": scene.transition or "cut"
            })

        # 4. Concatenate scenes if multiple
        if len(scene_clips) > 1:
            server_state.task_manager.update_task(
                task_id, progress=95, message="Concatenating scenes..."
            )
            final_video_name = _concat_scenes(scene_clips)
        else:
            final_video_name = scene_clips[0]["video_path"]

        # 5. Generate and optionally burn subtitles
        srt_path_name = None
        if request.subtitle_enabled:
            try:
                scene_durations = [sc["duration"] for sc in scene_clips]
                srt_content = generate_srt(scenes, scene_durations)
                srt_filename = f"{Path(final_video_name).stem}.srt"
                srt_path = VIDEO_OUTPUT_DIR / srt_filename
                with open(srt_path, "w", encoding="utf-8") as f:
                    f.write(srt_content)
                srt_path_name = srt_filename
                logger.info(f"Generated multi-scene subtitles: {srt_filename}")
                
                # Burn subtitles into the video
                server_state.task_manager.update_task(
                    task_id, progress=98, message="Burning subtitles into video..."
                )
                final_video_name = burn_subtitles(
                    str(VIDEO_OUTPUT_DIR / final_video_name),
                    str(srt_path),
                    position=request.subtitle_position or "bottom",
                    font_size=request.subtitle_font_size or 24
                )
                # burn_subtitles returns the full path (or name if we adjusted it, 
                # but based on my implementation it returns 'out' which is a path string)
                # I should make sure it returns just the filename if that's what we expect.
                final_video_name = Path(final_video_name).name
                
            except Exception as srt_err:
                logger.error(f"Failed to generate or burn subtitles: {srt_err}")

        server_state.task_manager.update_task(
            task_id,
            status=server_state.TaskStatus.COMPLETED,
            progress=100,
            message="Narrated video ready",
            result={
                "video_path": final_video_name, 
                "srt_path": srt_path_name,
                "scenes": total
            },
        )
    except Exception as e:
        logger.error(f"Narrated video task {task_id} failed: {e}", exc_info=True)
        server_state.task_manager.update_task(
            task_id,
            status=server_state.TaskStatus.FAILED,
            error=str(e),
            message=f"Narrated video generation failed: {e}",
        )


def run_scene_preview_task(task_id: str, request: VideoGenerationRequest):
    """Background task for quick scene preview (single frame thumbnail)."""
    try:
        engine = _get_video_engine()
        server_state.task_manager.update_task(
            task_id,
            status=server_state.TaskStatus.PROCESSING,
            progress=10,
            message="Generating preview thumbnail...",
        )

        # Generate minimum stable frames (9)
        result = engine.generate_video(
            prompt=request.prompt,
            width=request.width,
            height=request.height,
            num_frames=9,
            guidance_scale=request.guidance_scale,
            num_inference_steps=15, # Faster steps for preview
            seed=request.seed,
        )

        # Extract first frame as thumbnail
        from moviepy import VideoFileClip
        video_path = result["path"]
        thumb_filename = f"thumb_{Path(video_path).stem}.jpg"
        thumb_path = VIDEO_OUTPUT_DIR / thumb_filename
        
        clip = VideoFileClip(video_path)
        clip.save_frame(str(thumb_path), t=0)
        clip.close()

        server_state.task_manager.update_task(
            task_id,
            status=server_state.TaskStatus.COMPLETED,
            progress=100,
            message="Preview ready",
            result={"thumbnail_path": thumb_filename, "video_path": result["filename"]},
        )
    except Exception as e:
        logger.error(f"Scene preview task {task_id} failed: {e}", exc_info=True)
        server_state.task_manager.update_task(
            task_id,
            status=server_state.TaskStatus.FAILED,
            error=str(e),
            message=f"Preview generation failed: {e}",
        )


@router.post("/preview-scene")
async def preview_scene(request: VideoGenerationRequest, background_tasks: BackgroundTasks):
    """Generate a quick thumbnail preview of a scene."""
    engine = _get_video_engine()
    if not engine.available:
        return {"error": "LTX-2 video generation is not available."}

    task_id = server_state.task_manager.create_task(
        "scene_preview", {"prompt": request.prompt[:50]}
    )
    background_tasks.add_task(run_scene_preview_task, task_id, request)
    return {"task_id": task_id, "status": server_state.TaskStatus.PENDING}


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
        "royal": "opulent royal chamber, gold accents, velvet textures, warm candlelight, majestic lighting",
        "documentary": "high-contrast documentary style, handheld camera, natural lighting, authentic textures",
        "tutorial": "clean studio setup, soft even lighting, professional presenter framing, minimal distractions",
        "comedy": "bright colorful setting, warm playful lighting, wide comedic framing, exaggerated expressions",
        "romantic": "soft warm tones, golden hour backlighting, shallow depth of field, intimate close-ups",
        "action": "dynamic camera movement, high-speed tracking, explosive lighting, adrenaline-pumping visuals"
    }
    
    characters = {
        "person": "medium shot of a person",
        "scientist": "focused scientist in lab coat, examining equipment",
        "teacher": "friendly teacher gesturing towards a whiteboard",
        "narrator": "professional narrator seated at a desk, looking at camera",
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
    # Find matching character or use default
    for key, desc in characters.items():
        if key in text:
            subject = f"{desc} ({subject})"
            break

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
        f"{lens}, {palette}, {style}, professional color grading, ultra-high resolution, "
        "best quality, 4K, HDR, no watermark, no text overlay."
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
        "narrated_video", {"prompt": (request.prompt or "multi-scene")[:100]}
    )
    background_tasks.add_task(run_narrated_video_task, task_id, request)
    return {"task_id": task_id, "status": server_state.TaskStatus.PENDING}


@router.post("/narrated/batch")
async def batch_narrated_videos(requests: list[NarratedVideoRequest], background_tasks: BackgroundTasks):
    """Submit multiple narrated video jobs at once."""
    engine = _get_video_engine()
    if not engine.available:
        return {"error": "LTX-2 video generation is not available."}
    
    task_ids = []
    for i, req in enumerate(requests):
        desc = (req.prompt or f"Batch Item {i+1}")[:50]
        task_id = server_state.task_manager.create_task(
            "narrated_video", {"prompt": desc, "batch_index": i}
        )
        background_tasks.add_task(run_narrated_video_task, task_id, req)
        task_ids.append(task_id)
    
    return {"task_ids": task_ids, "total": len(task_ids)}


@router.get("/{filename}")
async def serve_video(filename: str):
    """Serve a generated video file."""
    # Security: only serve from VIDEO_OUTPUT_DIR, block path traversal
    safe_name = Path(filename).name
    video_path = VIDEO_OUTPUT_DIR / safe_name

    if not video_path.exists():
        return {"error": "Video not found"}

    return FileResponse(str(video_path), media_type="video/mp4", filename=safe_name)
