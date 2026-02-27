import os
import uuid
from pathlib import Path
from moviepy import VideoFileClip
from .config import logger, VIDEO_DIR

class VideoEngine:
    @staticmethod
    def extract_audio(video_path: str) -> str:
        """
        Extracts audio from a video file and saves it as a WAV file.
        Returns the path to the extracted audio file.
        """
        try:
            logger.info(f"Extracting audio from video: {video_path}")
            video = VideoFileClip(video_path)

            if video.audio is None:
                raise ValueError("Video file has no audio track.")

            audio_filename = f"ext_{uuid.uuid4()}.wav"
            audio_path = VIDEO_DIR / audio_filename

            video.audio.write_audiofile(str(audio_path), codec='pcm_s16le', verbose=False, logger=None)
            video.close()

            logger.info(f"Audio extracted successfully to: {audio_path}")
            return str(audio_path)
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            raise RuntimeError(f"Failed to extract audio from video: {e}")

    @staticmethod
    def is_video(file_path: str) -> bool:
        """Checks if a file is a video based on its extension."""
        video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.webm'}
        return Path(file_path).suffix.lower() in video_extensions
