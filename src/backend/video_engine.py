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

    def _get_font(self, size: int, font_name: str = "DejaVuSans-Bold.ttf"):
        # Try to find the requested font
        search_paths = [
            Path("/usr/share/fonts/truetype/dejavu"),
            Path("/usr/share/fonts/truetype/liberation"),
            Path("src/static/fonts")
        ]
        for p in search_paths:
            font_path = p / font_name
            if font_path.exists():
                return ImageFont.truetype(str(font_path), size)

        # Fallback to any available font
        for p in search_paths:
            if p.exists():
                for f in p.glob("*.ttf"):
                    return ImageFont.truetype(str(f), size)

        return ImageFont.load_default()

    def _create_text_image(self, text: str, width: int, height: int, font_size: int = 40, font_type: str = "DejaVuSans-Bold.ttf"):
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = self._get_font(font_size, font_type)

        # Simple wrapping
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            w = draw.textlength(" ".join(current_line), font=font)
            if w > width * 0.8:
                lines.append(" ".join(current_line[:-1]))
                current_line = [word]
        lines.append(" ".join(current_line))

        # Render lines from bottom
        line_height = font_size + 10
        total_height = len(lines) * line_height
        y = height - total_height - 50

        for line in lines:
            w = draw.textlength(line, font=font)
            x = (width - w) / 2
            # Shadow
            draw.text((x+2, y+2), line, font=font, fill=(0, 0, 0, 180))
            # Text
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
            y += line_height

        return np.array(img)

    def generate_video(self, project: ProjectData, aspect_ratio: str = "16:9", include_subtitles: bool = True, font_size: int = 40, font_type: str = "DejaVuSans-Bold.ttf") -> Path:
        logger.info(f"Starting video generation for project: {project.name}")

        if aspect_ratio == "16:9":
            w, h = 1920, 1080
        else: # 9:16
            w, h = 1080, 1920

        clips = []
        audio_clips = []
        current_time = 0.0

        # Map speakers to images
        speaker_images = {s["role"]: s.get("image_url") for s in project.voices}

        # Temporary directory for segment audio
        temp_audio_dir = Path("temp_audio")
        temp_audio_dir.mkdir(exist_ok=True)

        for i, block in enumerate(project.blocks):
            # 1. Generate Audio Segment
            try:
                wav, sr = self.podcast_engine.generate_segment(block.role, block.text, block.language)
                audio_path = temp_audio_dir / f"segment_{i}.wav"
                sf.write(str(audio_path), wav, sr)

                audio_clip = AudioFileClip(str(audio_path))
                duration = audio_clip.duration

                # 2. Get Visual
                img_url = block.image_url or speaker_images.get(block.role)
                if img_url and img_url.startswith("/api/voice/image/"):
                    img_name = img_url.split("/")[-1]
                    img_path = VOICE_IMAGES_DIR / img_name
                else:
                    img_path = None

                if img_path and img_path.exists():
                    img = Image.open(img_path).convert("RGB")
                    # Resize and Crop to match aspect ratio
                    img_w, img_h = img.size
                    target_ratio = w / h
                    current_ratio = img_w / img_h

                    if current_ratio > target_ratio:
                        # Too wide
                        new_w = int(img_h * target_ratio)
                        offset = (img_w - new_w) // 2
                        img = img.crop((offset, 0, offset + new_w, img_h))
                    else:
                        # Too tall
                        new_h = int(img_w / target_ratio)
                        offset = (img_h - new_h) // 2
                        img = img.crop((0, offset, img_w, offset + new_h))

                    img = img.resize((w, h), Image.Resampling.LANCZOS)
                    img_clip = ImageClip(np.array(img)).with_duration(duration + block.pause_after)

                    # Apply Ken Burns (simple zoom)
                    # Note: Manual zoom implementation to avoid missing vfx.Zoom
                    def zoom_effect(t):
                        return 1.0 + 0.1 * (t / (duration + block.pause_after))

                    try:
                        # MoviePy 2.x resized can take a function
                        img_clip = img_clip.resized(zoom_effect)
                    except Exception as ze:
                        logger.warning(f"Zoom effect failed: {ze}")
                else:
                    # Fallback to color clip
                    img_clip = ColorClip(size=(w, h), color=(30, 30, 30)).with_duration(duration + block.pause_after)

                # 3. Add Subtitles
                if include_subtitles:
                    txt_img = self._create_text_image(block.text, w, h, font_size, font_type)
                    txt_clip = ImageClip(txt_img).with_duration(duration).with_position(("center", "center"))
                    segment_clip = CompositeVideoClip([img_clip, txt_clip])
                else:
                    segment_clip = img_clip

                segment_clip = segment_clip.with_start(current_time)
                audio_clip = audio_clip.with_start(current_time)

                clips.append(segment_clip)
                audio_clips.append(audio_clip)

                current_time += duration + block.pause_after

            except Exception as e:
                block.status = "failed"

                logger.error(f"Failed to process block {i}: {e}")
                continue

        if not clips:
            raise RuntimeError("No clips generated")

        # 4. Final Composition
        final_video = CompositeVideoClip(clips)
        final_audio = CompositeAudioClip(audio_clips)

        # Add BGM if needed (optional for now, can be expanded)

        final_video = final_video.with_audio(final_audio)

        output_path = VIDEO_OUTPUT_DIR / f"{project.name.replace(' ', '_')}_{int(current_time)}s.mp4"

        logger.info(f"Writing final video to {output_path}")
        final_video.write_videofile(str(output_path), fps=24, codec="libx264", audio_codec="aac")

        # Cleanup temp audio
        for f in temp_audio_dir.glob("*.wav"):
            f.unlink()
        temp_audio_dir.rmdir()

        return output_path
