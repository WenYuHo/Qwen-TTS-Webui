import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    ImageClip,
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    VideoClip,
    ColorClip,
    vfx
)
import soundfile as sf
from .config import VIDEO_OUTPUT_DIR, VOICE_IMAGES_DIR, logger
from .api.schemas import ProjectData

class VideoEngine:
    def __init__(self, podcast_engine):
        self.podcast_engine = podcast_engine

    def _get_font(self, size: int, font_name: str = "DejaVuSans-Bold.ttf") -> ImageFont.ImageFont:
        """Find and load a TTF font, with fallbacks."""
        search_paths = [
            Path("/usr/share/fonts/truetype/dejavu"),
            Path("/usr/share/fonts/truetype/liberation"),
            Path("src/static/fonts"),
            Path("/usr/share/fonts/TTF")
        ]

        # 1. Try requested font
        for p in search_paths:
            font_path = p / font_name
            if font_path.exists():
                return ImageFont.truetype(str(font_path), size)

        # 2. Try any TTF in search paths
        for p in search_paths:
            if p.exists():
                for f in p.glob("*.ttf"):
                    return ImageFont.truetype(str(f), size)

        # 3. Last resort
        return ImageFont.load_default()

    def _create_text_image(self, text: str, width: int, height: int, font_size: int = 40, font_type: str = "DejaVuSans-Bold.ttf") -> np.ndarray:
        """Create a transparent RGBA image with wrapped text and shadow."""
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = self._get_font(font_size, font_type)

        # Robust wrapping
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            # Use draw.textbbox for more accurate measurement in modern PIL
            bbox = draw.textbbox((0, 0), " ".join(current_line), font=font)
            line_w = bbox[2] - bbox[0]
            if line_w > width * 0.85:
                if len(current_line) > 1:
                    lines.append(" ".join(current_line[:-1]))
                    current_line = [word]
                else: # Single word too long
                    lines.append(" ".join(current_line))
                    current_line = []
        if current_line:
            lines.append(" ".join(current_line))

        # Render lines from bottom
        line_height = font_size + 12
        total_height = len(lines) * line_height
        y = height - total_height - 80 # Padding from bottom

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            x = (width - line_w) / 2
            # Shadow for readability
            draw.text((x+2, y+2), line, font=font, fill=(0, 0, 0, 200))
            # Main white text
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            y += line_height

        return np.array(img)

    def _process_image(self, img_path: Path, target_w: int, target_h: int) -> Image.Image:
        """Resize and crop image to fill target dimensions while maintaining aspect ratio."""
        img = Image.open(img_path).convert("RGB")
        img_w, img_h = img.size
        target_ratio = target_w / target_h
        current_ratio = img_w / img_h

        if current_ratio > target_ratio:
            # Too wide, crop sides
            new_w = int(img_h * target_ratio)
            offset = (img_w - new_w) // 2
            img = img.crop((offset, 0, offset + new_w, img_h))
        else:
            # Too tall, crop top/bottom
            new_h = int(img_w / target_ratio)
            offset = (img_h - new_h) // 2
            img = img.crop((0, offset, img_w, offset + new_h))

        return img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    def _apply_ken_burns(self, clip: ImageClip, duration: float) -> ImageClip:
        """Apply a smooth zoom-in effect (Ken Burns)."""
        def zoom_func(t):
            return 1.0 + 0.1 * (t / duration)

        try:
            return clip.resized(zoom_func)
        except Exception as e:
            logger.warning(f"Ken Burns zoom failed: {e}")
            return clip

    def generate_video(self, project: ProjectData, aspect_ratio: str = "16:9", include_subtitles: bool = True, font_size: int = 40, font_type: str = "DejaVuSans-Bold.ttf", progress_callback=None) -> Path:
        """Orchestrate the full video generation from project blocks."""
        logger.info(f"Generating {aspect_ratio} video for: {project.name}")

        w, h = (1920, 1080) if aspect_ratio == "16:9" else (1080, 1920)
        clips = []
        audio_clips = []
        current_time = 0.0

        # Pre-map speaker images
        speaker_images = {s["role"]: s.get("image_url") for s in project.voices}

        temp_dir = Path("temp_video_assets")
        temp_dir.mkdir(exist_ok=True)

        try:
            for i, block in enumerate(project.blocks):
                try:
                    # 1. Audio
                    wav, sr = self.podcast_engine.generate_segment(block.role, block.text, block.language)
                    audio_path = temp_dir / f"seg_{i}.wav"
                    sf.write(str(audio_path), wav, sr)

                    audio_clip = AudioFileClip(str(audio_path))
                    duration = audio_clip.duration
                    full_duration = duration + block.pause_after

                    # 2. Visual Base
                    img_url = block.image_url or speaker_images.get(block.role)
                    img_path = None
                    if img_url and img_url.startswith("/api/voice/image/"):
                        img_path = VOICE_IMAGES_DIR / img_url.split("/")[-1]

                    if img_path and img_path.exists():
                        processed_img = self._process_image(img_path, w, h)
                        img_clip = ImageClip(np.array(processed_img)).with_duration(full_duration)
                        img_clip = self._apply_ken_burns(img_clip, full_duration)
                    else:
                        img_clip = ColorClip(size=(w, h), color=(25, 25, 30)).with_duration(full_duration)

                    # 3. Subtitles
                    if include_subtitles and block.text.strip():
                        txt_arr = self._create_text_image(block.text, w, h, font_size, font_type)
                        txt_clip = ImageClip(txt_arr).with_duration(duration).with_position(("center", "center"))
                        # Layer text on top of image
                        segment_clip = CompositeVideoClip([img_clip, txt_clip])
                    else:
                        segment_clip = img_clip

                    # 4. Timing
                    clips.append(segment_clip.with_start(current_time))
                    audio_clips.append(audio_clip.with_start(current_time))

                    current_time += full_duration
                    if progress_callback:
                        progress_callback(int(20 + 70 * (i + 1) / len(project.blocks)))

                except Exception as e:
                    logger.error(f"Error in block {i} ({block.role}): {e}")
                    block.status = "failed"
                    continue

            if not clips:
                raise RuntimeError("No valid clips were generated for this video.")

            # 5. Final Composition
            final_v = CompositeVideoClip(clips)
            final_a = CompositeAudioClip(audio_clips)
            final_v = final_v.with_audio(final_a)

            output_file = VIDEO_OUTPUT_DIR / f"{project.name.replace(' ', '_')}_{int(current_time)}s.mp4"
            logger.info(f"Rendering final MP4 to {output_file}")

            final_v.write_videofile(
                str(output_file),
                fps=24,
                codec="libx264",
                audio_codec="aac",
                threads=os.cpu_count(),
                logger=None # Suppress MoviePy verbose output
            )

            return output_file

        finally:
            # Cleanup
            for f in temp_dir.glob("seg_*.wav"):
                try: f.unlink()
                except: pass
            try: temp_dir.rmdir()
            except: pass
