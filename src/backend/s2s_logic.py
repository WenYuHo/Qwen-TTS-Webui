from .task_manager import task_manager, TaskStatus
from .podcast_engine import PodcastEngine
from .utils import numpy_to_wav_bytes

def run_s2s_task(task_id, source_audio, target_voice, engine: PodcastEngine):
    try:
        task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=10, message="Transcribing source audio...")

        # 1. Transcribe
        text = engine.transcribe_audio(source_audio)

        task_manager.update_task(task_id, progress=50, message="Synthesizing with target voice...")

        # 2. Setup target voice
        profile = {"type": target_voice["type"], "value": target_voice["value"]}

        # 3. Generate
        wav, sr = engine.generate_segment(text, profile=profile)

        task_manager.update_task(task_id, progress=90, message="Encoding audio...")

        wav_bytes = numpy_to_wav_bytes(wav, sr).read()
        task_manager.update_task(task_id, status=TaskStatus.COMPLETED, progress=100, message="Ready", result=wav_bytes)

    except Exception as e:
        from .config import logger
        logger.error(f"S2S Task {task_id} failed: {e}", exc_info=True)
        task_manager.update_task(task_id, status=TaskStatus.FAILED, error="S2S error", message="S2S failed. Please check your inputs or logs.")
