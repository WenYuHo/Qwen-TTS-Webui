"""LTX-2 Video Generation Engine.

Wraps the LTX-2 DistilledPipeline for text-to-video generation.
Requires ltx-pipelines package and downloaded model checkpoints.
"""
import os
import uuid
import threading
from pathlib import Path
from typing import Optional, Dict, Any

from ..config import (
    logger,
    LTX_MODELS_PATH,
    VIDEO_OUTPUT_DIR,
    find_ltx_model,
    is_ltx_available,
)


class LTXVideoEngine:
    """Lazy-loading wrapper around LTX-2 DistilledPipeline for video generation."""

    def __init__(self):
        self._pipeline = None
        self._lock = threading.Lock()
        self._available = None  # lazy check

    @property
    def available(self) -> bool:
        """Check if LTX-2 models are present and the package is installed."""
        if self._available is None:
            try:
                import ltx_pipelines  # noqa: F401
                self._available = is_ltx_available()
            except ImportError:
                logger.info("ltx-pipelines not installed — video generation disabled")
                self._available = False
        return self._available

    def _ensure_pipeline(self):
        """Lazy-load the best available LTX pipeline on first use."""
        if self._pipeline is not None:
            return

        with self._lock:
            if self._pipeline is not None:
                return

            if not self.available:
                raise RuntimeError(
                    "No LTX models found. Go to System > Model Inventory to download them."
                )

            # Check for LTX-2 (19B Distilled)
            checkpoint_19b = find_ltx_model("checkpoint")
            gemma_dir = find_ltx_model("gemma_dir")
            spatial_upsampler = find_ltx_model("spatial_upsampler")

            # Check for LTX-Video (2B/13B)
            checkpoint_ltxv = find_ltx_model("ltxv_checkpoint")

            if checkpoint_19b and gemma_dir:
                from ltx_pipelines.distilled import DistilledPipeline
                logger.info(f"Loading LTX-2 (19B) DistilledPipeline from {checkpoint_19b.parent}")
                
                pipeline_kwargs = {
                    "checkpoint_path": str(checkpoint_19b),
                    "gemma_root": str(gemma_dir),
                    "fp8transformer": True,
                }
                if spatial_upsampler:
                    pipeline_kwargs["spatial_upsampler_path"] = str(spatial_upsampler)
                
                self._pipeline = DistilledPipeline(**pipeline_kwargs)
                self._model_type = "ltx-2"

            elif checkpoint_ltxv:
                # LTX-Video (v0.9) support
                try:
                    from ltx_pipelines.t2v import LTXVideoPipeline
                except ImportError:
                    # Fallback for older versions of the package
                    from ltx_pipelines.pipelines.t2v import LTXVideoPipeline

                logger.info(f"Loading LTX-Video (2B/13B) from {checkpoint_ltxv}")
                self._pipeline = LTXVideoPipeline(
                    checkpoint_path=str(checkpoint_ltxv),
                    fp8transformer=True
                )
                self._model_type = "ltx-video"
            
            if self._pipeline:
                logger.info(f"LTX Engine initialized with {self._model_type}")
                
                # --- ⚡ Bolt: LTX-Video Performance Optimizations ---
                import torch
                
                # 1. VAE Memory Reduction (Prevents OOM during final decode)
                if hasattr(self._pipeline, "vae") and hasattr(self._pipeline.vae, "enable_slicing"):
                    self._pipeline.vae.enable_slicing()
                    logger.info("Enabled VAE slicing for memory reduction.")
                elif hasattr(self._pipeline, "vae") and hasattr(self._pipeline.vae, "enable_tiling"):
                    self._pipeline.vae.enable_tiling()
                    logger.info("Enabled VAE tiling for memory reduction.")

                # 2. Xformers / Memory Efficient Attention
                try:
                    import xformers  # noqa: F401
                    if hasattr(self._pipeline, "enable_xformers_memory_efficient_attention"):
                        self._pipeline.enable_xformers_memory_efficient_attention()
                        logger.info("Enabled xformers memory efficient attention.")
                except ImportError:
                    logger.info("xformers not installed. Using PyTorch SDPA (default).")
                    
                # 3. CPU Offloading (Crucial for 8GB/12GB GPUs running Video Gen)
                if hasattr(self._pipeline, "enable_model_cpu_offload"):
                    self._pipeline.enable_model_cpu_offload()
                    logger.info("Enabled model CPU offloading.")

                # 4. PyTorch 2.0 Compilation (Speed boost)
                if hasattr(torch, "compile") and hasattr(self._pipeline, "transformer"):
                    try:
                        # mode="reduce-overhead" is often best for video gen
                        self._pipeline.transformer = torch.compile(self._pipeline.transformer, mode="reduce-overhead", fullgraph=True)
                        logger.info("Applied torch.compile() to LTX transformer for speed optimization.")
                    except Exception as e:
                        logger.warning(f"Failed to torch.compile transformer (safe to ignore): {e}")

            else:
                raise RuntimeError("Failed to resolve an LTX model path.")


    def _apply_video_watermark(self, video_path: str):
        """Overlays a subtle 'AI Generated' text watermark using OpenCV."""
        try:
            from ..api.system import _settings
            if not _settings.watermark_video:
                return
            
            import cv2
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Temporary output path
            temp_path = video_path.replace(".mp4", "_wm.mp4")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_path, fourcc, fps, (w, h))
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Overlay text
                text = "AI Generated"
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(frame, text, (w - 150, h - 20), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                out.write(frame)
                
            cap.release()
            out.release()
            
            # Replace original with watermarked
            import os
            os.replace(temp_path, video_path)
        except Exception as e:
            logger.error(f"Failed to apply video watermark: {e}")

    def generate_video(
        self,
        prompt: str,
        width: int = 768,
        height: int = 512,
        num_frames: int = 65,
        guidance_scale: float = 3.5,
        num_inference_steps: int = 30,
        seed: Optional[int] = None,
        max_shift: Optional[float] = None,
        base_shift: Optional[float] = None,
        terminal: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Generate a video from a text prompt.

        Returns:
            dict with 'path' (str) to the generated MP4 file and 'filename' (str).
        """
        self._ensure_pipeline()

        filename = f"vid_{uuid.uuid4().hex[:12]}.mp4"
        output_path = VIDEO_OUTPUT_DIR / filename

        logger.info(f"Generating video: prompt='{prompt[:80]}...', {width}x{height}, {num_frames} frames")

        pipeline_kwargs = {
            "prompt": prompt,
            "output_path": str(output_path),
            "width": width,
            "height": height,
            "num_frames": num_frames,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_inference_steps,
        }

        if seed is not None and seed != -1:
            pipeline_kwargs["seed"] = seed
            
        # ⚡ Bolt: Advanced LTX-2 Shift Parameters for motion control
        if max_shift is not None: pipeline_kwargs["max_shift"] = max_shift
        if base_shift is not None: pipeline_kwargs["base_shift"] = base_shift
        if terminal is not None: pipeline_kwargs["terminal"] = terminal

        self._pipeline(**pipeline_kwargs)
        
        # Apply watermark
        self._apply_video_watermark(str(output_path))

        # --- ⚡ Bolt: Aggressive VRAM Cleanup ---
        import gc
        import torch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            
        logger.info(f"Video generated: {output_path}. VRAM cleared.")
        return {"path": str(output_path), "filename": filename}

    def generate_narrated_video(
        self,
        prompt: str,
        narration_wav,
        narration_sr: int,
        width: int = 768,
        height: int = 512,
        num_frames: int = 65,
        guidance_scale: float = 3.5,
        num_inference_steps: int = 30,
        seed: Optional[int] = None,
        max_shift: Optional[float] = None,
        base_shift: Optional[float] = None,
        terminal: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Generate video and combine with narration audio into a single MP4.

        Args:
            prompt: Text prompt for video generation.
            narration_wav: numpy array of TTS audio.
            narration_sr: Sample rate of the narration audio.
            width/height/num_frames/seed: Video generation parameters.

        Returns:
            dict with 'path' to the combined MP4.
        """
        import numpy as np
        import soundfile as sf
        from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

        # 1. Generate the video
        video_result = self.generate_video(
            prompt=prompt,
            width=width,
            height=height,
            num_frames=num_frames,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            seed=seed,
            max_shift=max_shift,
            base_shift=base_shift,
            terminal=terminal,
        )

        # 2. Save narration audio to temp WAV
        narration_filename = f"narr_{uuid.uuid4().hex[:12]}.wav"
        narration_path = VIDEO_OUTPUT_DIR / narration_filename
        sf.write(str(narration_path), narration_wav, narration_sr)

        # 3. Combine video + audio using MoviePy
        output_filename = f"narrated_{uuid.uuid4().hex[:12]}.mp4"
        output_path = VIDEO_OUTPUT_DIR / output_filename

        try:
            video_clip = VideoFileClip(video_result["path"])
            narration_clip = AudioFileClip(str(narration_path))

            # If video has existing audio, mix them; otherwise just set narration
            if video_clip.audio is not None:
                combined_audio = CompositeAudioClip([video_clip.audio, narration_clip])
                final_clip = video_clip.with_audio(combined_audio)
            else:
                final_clip = video_clip.with_audio(narration_clip)

            final_clip.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                verbose=False,
                logger=None,
            )

            video_clip.close()
            narration_clip.close()
        finally:
            # Cleanup temp narration file
            try:
                narration_path.unlink(missing_ok=True)
            except Exception:
                pass

        logger.info(f"Narrated video generated: {output_path}")
        return {"path": str(output_path), "filename": output_filename}

    def get_status(self) -> Dict[str, Any]:
        """Return status info about LTX-2 availability."""
        return {
            "available": self.available,
            "models_dir": str(LTX_MODELS_PATH),
            "pipeline_loaded": self._pipeline is not None,
            "models_found": {
                key: find_ltx_model(key) is not None
                for key in ["checkpoint", "spatial_upsampler", "distilled_lora", "gemma_dir"]
            },
        }
