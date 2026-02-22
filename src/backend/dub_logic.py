from .task_manager import task_manager, TaskStatus
from .podcast_engine import PodcastEngine
from .utils import numpy_to_wav_bytes

def run_dub_task(task_id, source_audio, target_lang, engine: PodcastEngine):
    try:
        task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=10, message="Processing audio...")

        result = engine.dub_audio(source_audio, target_lang)

        task_manager.update_task(task_id, progress=90, message="Encoding audio...")

        wav_bytes = numpy_to_wav_bytes(result["waveform"], result["sample_rate"]).read()
        task_manager.update_task(task_id, status=TaskStatus.COMPLETED, progress=100, message="Ready", result=wav_bytes)

    except Exception as e:
        task_manager.update_task(task_id, status=TaskStatus.FAILED, error=str(e), message=f"Dubbing failed: {e}")
