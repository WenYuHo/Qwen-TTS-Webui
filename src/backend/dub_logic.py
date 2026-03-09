from .task_manager import task_manager, TaskStatus
from .podcast_engine import PodcastEngine
from .utils import numpy_to_wav_bytes
from .config import logger
import hashlib
import numpy as np
import soundfile as sf
import librosa
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
            
            # Resolve source path to get duration
            resolved = engine._resolve_paths(source_audio)
            source_path = str(resolved[0])
            info = sf.info(source_path)
            sr_out = 24000
            final_wav = np.zeros(int(info.duration * sr_out), dtype=np.float32)
            
            failed_segments = []
            MAX_RETRIES = 2

            # Group segments by speaker
            for i, seg in enumerate(segments):
                seg_text = seg["text"].strip()
                if not seg_text: continue
                
                success = False
                for attempt in range(MAX_RETRIES + 1):
                    try:
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

                        # ⚡ Bolt: Precise Timing Refinement
                        # 1. Trim trailing/leading silence
                        wav, _ = librosa.effects.trim(wav, top_db=20)

                        # 2. Resample if needed
                        if sr != sr_out:
                            wav = librosa.resample(wav, orig_sr=sr, target_sr=sr_out)

                        # 3. Time-stretch to fit if too long (max 1.2x speedup)
                        orig_duration = seg["end"] - seg["start"]
                        synth_duration = len(wav) / sr_out

                        if synth_duration > orig_duration:
                            rate = synth_duration / orig_duration
                            if rate <= 1.2: # Only stretch if within reasonable bounds
                                logger.info(f"⚡ Bolt: Time-stretching segment {i} by {rate:.2f}x to fit.")
                                wav = librosa.effects.time_stretch(wav, rate=rate)
                            else:
                                # If way too long, just truncate to avoid bleeding into next segment
                                wav = wav[:int(orig_duration * sr_out)]

                        # Place in timeline
                        start_sample = int(seg["start"] * sr_out)
                        end_sample = min(start_sample + len(wav), len(final_wav))
                        final_wav[start_sample:end_sample] = wav[:end_sample - start_sample]
                        success = True

                        break
                    except Exception as e:
                        if attempt < MAX_RETRIES:
                            import time
                            time.sleep(1) # Brief pause before retry
                            continue
                        else:
                            print(f"Failed segment {i} after {MAX_RETRIES} retries: {e}")
                            failed_segments.append(i)
                
                progress = int(40 + ((i + 1) / len(segments)) * 50)
                msg = f"Synthesizing segment {i+1}/{len(segments)}"
                if failed_segments:
                    msg += f" ({len(failed_segments)} failed)"
                task_manager.update_task(task_id, progress=progress, message=msg)
            
            wav = final_wav
            sr = sr_out
            translated_text = "[Multi-speaker dubbed]"
            if failed_segments:
                translated_text += f" (Note: {len(failed_segments)} segments failed)"
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
        
        result_data = {
            "audio": wav_bytes,
            "segments": segments,
            "mouth_cues": mouth_cues
        }
        
        if speaker_assignment and len(segments) > 0 and failed_segments:
            result_data["warnings"] = f"{len(failed_segments)} segments failed to synthesize and were skipped."

        task_manager.update_task(task_id, status=TaskStatus.COMPLETED, progress=100, message="Ready", result=result_data)

    except Exception as e:
        task_manager.update_task(task_id, status=TaskStatus.FAILED, error=str(e), message=f"Dubbing failed: {e}")
