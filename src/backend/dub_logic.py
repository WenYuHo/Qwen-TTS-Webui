from .task_manager import task_manager, TaskStatus
from .podcast_engine import PodcastEngine
from .utils import numpy_to_wav_bytes
import hashlib
from deep_translator import GoogleTranslator

def run_dub_task(task_id, source_audio, target_lang, engine: PodcastEngine):
    try:
        task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=10, message="Transcribing source audio...")

        # 1. Transcribe
        result = engine.transcribe_audio(source_audio)
        text = result["text"]
        detected_lang = result["language"]
        
        task_manager.update_task(task_id, progress=30, message=f"Detected {detected_lang}. Translating to {target_lang}...")

        # 2. Translate (using logic similar to engine.dub_audio for consistency/cache)
        trans_lang = 'zh-CN' if target_lang == 'zh' else target_lang
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        cache_key = f"{text_hash}:{trans_lang}"

        if cache_key in engine.translation_cache:
            translated_text = engine.translation_cache[cache_key]
        else:
            # Note: We use engine.translation_cache so it's shared
            translated_text = GoogleTranslator(source='auto', target=trans_lang).translate(text)
            engine.translation_cache[cache_key] = translated_text

        task_manager.update_task(task_id, progress=60, message="Synthesizing dubbed audio...")

        # 3. Synthesize
        wav, sr = engine.generate_segment(translated_text, profile={"type": "clone", "value": source_audio}, language=target_lang)

        task_manager.update_task(task_id, progress=90, message="Encoding audio...")

        # 4. Finalize
        wav_bytes = numpy_to_wav_bytes(wav, sr).read()
        task_manager.update_task(task_id, status=TaskStatus.COMPLETED, progress=100, message="Ready", result={
            "audio": wav_bytes,
            "segments": result.get("segments", [])
        })

    except Exception as e:
        task_manager.update_task(task_id, status=TaskStatus.FAILED, error=str(e), message=f"Dubbing failed: {e}")
