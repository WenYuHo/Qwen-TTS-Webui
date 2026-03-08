import io
import zipfile
import os
from .task_manager import task_manager, TaskStatus
from .podcast_engine import PodcastEngine
from .utils import numpy_to_wav_bytes

def run_s2s_task(task_id, source_audio, target_voice, engine: PodcastEngine, preserve_prosody: bool = True, instruct: str = None):
    try:
        task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=10, message="Transcribing source audio...")

        # 1. Transcribe
        result = engine.transcribe_audio(source_audio)
        text = result["text"]

        task_manager.update_task(task_id, progress=50, message="Synthesizing with target voice...")

        # 2. Setup target voice
        profile = {"type": target_voice["type"], "value": target_voice["value"]}

        # 3. Generate
        # ⚡ Bolt: Use generate_voice_changer for better S2S (ICL support)
        res = engine.generate_voice_changer(source_audio, profile, preserve_prosody=preserve_prosody, instruct=instruct)
        wav = res["waveform"]
        sr = res["sample_rate"]

        task_manager.update_task(task_id, progress=90, message="Encoding audio...")

        wav_bytes = numpy_to_wav_bytes(wav, sr).read()
        task_manager.update_task(task_id, status=TaskStatus.COMPLETED, progress=100, message="Ready", result=wav_bytes)

    except Exception as e:
        task_manager.update_task(task_id, status=TaskStatus.FAILED, error=str(e), message=f"S2S failed: {e}")

def run_batch_s2s_task(task_id, source_audios, target_voice, engine: PodcastEngine, preserve_prosody: bool = True, instruct: str = None):
    try:
        total = len(source_audios)
        results = []
        
        profile = {"type": target_voice["type"], "value": target_voice["value"]}

        for i, source in enumerate(source_audios):
            current_progress = int((i / total) * 90)
            task_manager.update_task(task_id, progress=current_progress, message=f"Processing {i+1}/{total}: {source}")
            
            try:
                res = engine.generate_voice_changer(source, profile, preserve_prosody=preserve_prosody, instruct=instruct)
                wav_bytes = numpy_to_wav_bytes(res["waveform"], res["sample_rate"]).read()
                results.append((source, wav_bytes))
            except Exception as e:
                print(f"Error processing {source}: {e}")
                continue

        if not results:
            raise Exception("All batch items failed")

        task_manager.update_task(task_id, progress=95, message="Creating ZIP archive...")
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for source, data in results:
                # Use original filename but with .wav extension for the result
                base_name = os.path.splitext(os.path.basename(source))[0]
                zip_file.writestr(f"{base_name}_converted.wav", data)
        
        task_manager.update_task(task_id, status=TaskStatus.COMPLETED, progress=100, message="Ready", result=zip_buffer.getvalue())

    except Exception as e:
        task_manager.update_task(task_id, status=TaskStatus.FAILED, error=str(e), message=f"Batch S2S failed: {e}")
