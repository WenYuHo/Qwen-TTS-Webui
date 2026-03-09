from .task_manager import task_manager, TaskStatus
from .podcast_engine import PodcastEngine
from .utils import numpy_to_wav_bytes
import hashlib
from deep_translator import GoogleTranslator

def run_dub_task(task_id, source_audio, target_lang, engine: PodcastEngine, speaker_assignment: dict = None):
    try:
        task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=10, message="Transcribing source audio...")

        # 1. Transcribe (includes segments with timestamps)
        result = engine.transcribe_audio(source_audio)
        text = result["text"]
        detected_lang = result["language"]
        segments = result.get("segments", [])
        
        task_manager.update_task(task_id, progress=30, message=f"Detected {detected_lang}. Translating...")

        # 2. Translation & Multi-Speaker Logic
        trans_lang = 'zh-CN' if target_lang == 'zh' else target_lang
        
        if speaker_assignment and len(segments) > 0:
            task_manager.update_task(task_id, progress=40, message="Starting multi-speaker synthesis...")
            
            import numpy as np
            import soundfile as sf
            
            # Resolve source path to get duration
            resolved = engine._resolve_paths(source_audio)
            source_path = str(resolved[0])
            info = sf.info(source_path)
            sr_out = 24000
            final_wav = np.zeros(int(info.duration * sr_out), dtype=np.float32)
            
            # Group segments by speaker
            for i, seg in enumerate(segments):
                seg_text = seg["text"].strip()
                if not seg_text: continue
                
                speaker_id = seg.get("speaker", "SPEAKER_00")
                # Default to a clone of the source if speaker not assigned
                voice_profile = speaker_assignment.get(speaker_id, {"type": "clone", "value": source_audio})
                
                # Translate segment
                seg_hash = hashlib.md5(seg_text.encode('utf-8')).hexdigest()
                seg_cache_key = f"{seg_hash}:{trans_lang}"
                if seg_cache_key in engine.translation_cache:
                    seg_translated = engine.translation_cache[seg_cache_key]
                else:
                    seg_translated = GoogleTranslator(source='auto', target=trans_lang).translate(seg_text)
                    engine.translation_cache[seg_cache_key] = seg_translated
                
                # Synthesize
                wav, sr = engine.generate_segment(seg_translated, profile=voice_profile, language=target_lang)
                
                # Place in timeline
                start_sample = int(seg["start"] * sr_out)
                # Resample wav if needed (engine usually returns 24k)
                if sr != sr_out:
                    import librosa
                    wav = librosa.resample(wav, orig_sr=sr, target_sr=sr_out)
                
                end_sample = min(start_sample + len(wav), len(final_wav))
                final_wav[start_sample:end_sample] = wav[:end_sample - start_sample]
                
                progress = int(40 + (i / len(segments)) * 50)
                task_manager.update_task(task_id, progress=progress, message=f"Synthesizing segment {i+1}/{len(segments)}")
            
            wav = final_wav
            sr = sr_out
            translated_text = "[Multi-speaker dubbed]"
        else:
            # Traditional single-speaker dub
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            cache_key = f"{text_hash}:{trans_lang}"

            if cache_key in engine.translation_cache:
                translated_text = engine.translation_cache[cache_key]
            else:
                translated_text = GoogleTranslator(source='auto', target=trans_lang).translate(text)
                engine.translation_cache[cache_key] = translated_text

            task_manager.update_task(task_id, progress=60, message="Synthesizing dubbed audio...")
            wav, sr = engine.generate_segment(translated_text, profile={"type": "clone", "value": source_audio}, language=target_lang)

        task_manager.update_task(task_id, progress=95, message="Encoding audio...")

        # 4. Finalize
        from .utils.lip_sync import generate_viseme_timestamps
        duration = len(wav) / sr
        mouth_cues = generate_viseme_timestamps(translated_text, duration, language=target_lang)

        wav_bytes = numpy_to_wav_bytes(wav, sr).read()
        task_manager.update_task(task_id, status=TaskStatus.COMPLETED, progress=100, message="Ready", result={
            "audio": wav_bytes,
            "segments": segments,
            "mouth_cues": mouth_cues
        })

    except Exception as e:
        task_manager.update_task(task_id, status=TaskStatus.FAILED, error=str(e), message=f"Dubbing failed: {e}")
