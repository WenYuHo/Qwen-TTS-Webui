import io
import json
import re
import soundfile as sf
import numpy as np
import time
import threading
from pathlib import Path
from .config import PROJECTS_DIR, BASE_DIR, logger

try:
    from scipy import signal as scipy_signal
except ImportError:
    scipy_signal = None

# ⚡ Bolt: Cache for Butterworth filter coefficients to avoid redundant DSP math
_eq_filter_cache = {}

def numpy_to_wav_bytes(waveform, sample_rate):
    """Converts a numpy waveform to a WAV-formatted BytesIO object."""
    if waveform.dtype != np.float32:
        waveform = waveform.astype(np.float32)
    buffer = io.BytesIO()
    sf.write(buffer, waveform, sample_rate, format='WAV')
    buffer.seek(0)
    return buffer

def validate_safe_path(full_path, base_dir):
    """Ensures the full_path is inside base_dir."""
    try:
        base = Path(base_dir).resolve()
        full = Path(full_path).resolve()
        return full.is_relative_to(base)
    except Exception:
        return False

class PhonemeManager:
    """Manages phonetic overrides for specific words to fix mispronunciations."""
    def __init__(self):
        self.file_path = PROJECTS_DIR / "phonemes.json"
        self.overrides = self._load()
        self.combined_pattern = None
        self.word_map = {}
        self._compile_combined()

    def _compile_combined(self):
        """Pre-compile a single combined regex pattern for high-performance single-pass replacement."""
        if not self.overrides:
            self.combined_pattern = None
            self.word_map = {}
            return

        # Sort words by length descending to ensure longest matches are tried first
        sorted_words = sorted(self.overrides.keys(), key=len, reverse=True)
        self.word_map = {word.lower(): word for word in self.overrides}

        pattern_str = r'\b(' + '|'.join(re.escape(w) for w in sorted_words) + r')\b'
        self.combined_pattern = re.compile(pattern_str, re.IGNORECASE)

    def _load(self):
        if not self.file_path.exists():
            return {}
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self, overrides):
        self.overrides = overrides
        self._compile_combined()
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.overrides, f, indent=2, ensure_ascii=False)

    def apply(self, text: str) -> str:
        """Replace words in text with their phonetic equivalents."""
        if not self.overrides or not self.combined_pattern:
            return text

        def _replacer(match):
            # ⚡ Bolt: Use O(1) dictionary lookup within a single-pass regex substitution
            word = match.group(0).lower()
            original_word = self.word_map.get(word)
            if original_word:
                return self.overrides.get(original_word, match.group(0))
            return match.group(0)

        return self.combined_pattern.sub(_replacer, text)

phoneme_manager = PhonemeManager()

class AudioPostProcessor:
    """Applies atmospheric effects like EQ and Reverb to final waveforms."""
    @staticmethod
    def apply_eq(wav: np.ndarray, sr: int, preset: str = "flat") -> np.ndarray:
        # ⚡ Bolt: Fast return for identity preset or missing dependency
        if preset == "flat" or scipy_signal is None:
            return wav

        try:
            # ⚡ Bolt: Cache coefficients (b, a) to avoid redundant scipy.signal.butter calls
            # This reduces CPU overhead significantly for multi-segment batch generation.
            cache_key = (preset, sr)
            if cache_key in _eq_filter_cache:
                b, a = _eq_filter_cache[cache_key]
            else:
                if preset == "broadcast":
                    b, a = scipy_signal.butter(2, [80 / (sr/2), 5000 / (sr/2)], btype='bandpass')
                elif preset == "warm":
                    b, a = scipy_signal.butter(2, 3000 / (sr/2), btype='low')
                elif preset == "bright":
                    b, a = scipy_signal.butter(2, 1000 / (sr/2), btype='high')
                else:
                    return wav
                _eq_filter_cache[cache_key] = (b, a)

            out = scipy_signal.lfilter(b, a, wav)
            if preset == "broadcast":
                out *= 1.5
            return out
        except Exception as e:
            logger.error(f"⚡ Bolt: EQ failed for {preset} at {sr}Hz: {e}")
            return wav

    @staticmethod
    def apply_reverb(wav: np.ndarray, sr: int, intensity: float = 0.0) -> np.ndarray:
        if intensity <= 0:
            return wav
        try:
            delay_samples = int(0.05 * sr)
            decay = intensity * 0.4
            out = wav.copy()
            # ⚡ Bolt: Handle both Mono and Stereo reverb
            is_stereo = len(wav.shape) == 2
            
            for i in range(1, 4):
                shift = delay_samples * i
                if is_stereo:
                    if shift < wav.shape[1]:
                        out[:, shift:] += wav[:, :-shift] * (decay ** i)
                else:
                    if shift < len(wav):
                        out[shift:] += wav[:-shift] * (decay ** i)
            
            max_amp = np.max(np.abs(out))
            if max_amp > 1.0:
                out /= max_amp
            return out
        except Exception:
            return wav

    @staticmethod
    def normalize_acx(wav: np.ndarray) -> np.ndarray:
        """Applies RMS normalization and peak limiting to meet ACX standards."""
        if len(wav) == 0:
            return wav
        try:
            # ⚡ Bolt: Handle multi-channel RMS calculation
            current_rms = np.sqrt(np.mean(wav**2))
            if current_rms > 0:
                target_rms = 0.1
                gain = target_rms / current_rms
                wav = wav * gain

            # 2. Peak Limiting: -3dB (approx 0.707 linear)
            max_peak = np.max(np.abs(wav))
            if max_peak > 0.707:
                wav = wav * (0.707 / max_peak)

            return wav.astype(np.float32)
        except Exception as e:
            logger.error(f"ACX normalization failed: {e}")
            return wav

    @staticmethod
    def apply_panning(wav: np.ndarray, pan: float = 0.0) -> np.ndarray:
        """Applies stereo panning to a mono signal.
        pan: -1.0 (Full Left) to 1.0 (Full Right)
        Returns: Stereo (2, N) numpy array.
        """
        if len(wav.shape) > 1:
            # Already stereo, or multi-channel
            return wav
            
        try:
            # Linear panning
            left = (1.0 - pan) / 2.0
            right = (1.0 + pan) / 2.0
            
            stereo = np.zeros((2, len(wav)), dtype=np.float32)
            stereo[0] = wav * left
            stereo[1] = wav * right
            return stereo
        except Exception as e:
            logger.error(f"Panning failed: {e}")
            return np.stack([wav, wav]) # Fallback to dual-mono

class AuditManager:
    """Logs system-wide AI generation events for transparency and tracking."""
    def __init__(self):
        self.file_path = PROJECTS_DIR / "audit.json"
        self.lock = threading.Lock()

    def log_event(self, event_type: str, metadata: dict, status: str):
        event = {
            "timestamp": time.time(),
            "type": event_type,
            "status": status,
            "metadata": self._sanitize_metadata(metadata)
        }
        with self.lock:
            log = self._load()
            log.append(event)
            if len(log) > 1000:
                log = log[-1000:]
            self._save(log)

    def _sanitize_metadata(self, metadata: dict) -> dict:
        sanitized = metadata.copy()
        for key in ["result", "wav", "waveform", "hidden_states"]:
            sanitized.pop(key, None)
        return sanitized

    def _load(self) -> list:
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, log: list):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)

    def get_log(self) -> list:
        return self._load()

class ResourceMonitor:
    """Provides real-time CPU, RAM, and GPU usage metrics."""
    @staticmethod
    def get_stats() -> dict:
        import psutil
        stats = {
            "cpu_percent": psutil.cpu_percent(),
            "ram_percent": psutil.virtual_memory().percent,
            "gpu": None
        }
        try:
            import torch
            if torch.cuda.is_available():
                gpu_id = torch.cuda.current_device()
                props = torch.cuda.get_device_properties(gpu_id)
                stats["gpu"] = {
                    "name": props.name,
                    "vram_total": props.total_memory / (1024**3),
                    "vram_used": torch.cuda.memory_allocated(gpu_id) / (1024**3),
                    "vram_percent": (torch.cuda.memory_allocated(gpu_id) / props.total_memory) * 100
                }
        except Exception:
            pass
        return stats

class StorageManager:
    """Manages disk space by periodically pruning stale generation artifacts."""
    def __init__(self, max_age_days: int = 7):
        self.max_age_days = max_age_days
        self.targets = [
            BASE_DIR / "uploads",
            PROJECTS_DIR / "generated_videos"
        ]
        self._stop_event = threading.Event()
        self._thread = None
        self.last_cleanup_time = 0
        self.total_pruned_count = 0

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="StorageCleanup")
        self._thread.start()
        logger.info(f"StorageManager started: pruning files older than {self.max_age_days} days.")

    def stop(self):
        self._stop_event.set()

    def _run_loop(self):
        while not self._stop_event.wait(86400):
            self.prune()

    def prune(self):
        now = time.time()
        max_age_seconds = self.max_age_days * 86400
        pruned_count = 0
        for target_dir in self.targets:
            if not target_dir.exists():
                continue
            for item in target_dir.iterdir():
                # Preservation: Never delete .gitkeep files
                if item.name == ".gitkeep":
                    continue
                if item.is_file():
                    try:
                        stat = item.stat()
                        if now - stat.st_mtime > max_age_seconds:
                            item.unlink()
                            pruned_count += 1
                    except Exception as e:
                        logger.error(f"Failed to prune {item}: {e}")
        
        self.last_cleanup_time = now
        self.total_pruned_count += pruned_count
        if pruned_count > 0:
            logger.info(f"StorageManager: Pruned {pruned_count} stale files.")

    def purge_cache(self):
        """Manually clear all temporary generation artifacts and engine caches."""
        pruned_count = 0
        for target_dir in self.targets:
            if not target_dir.exists():
                continue
            for item in target_dir.iterdir():
                # Preservation: Never delete infrastructure files
                if item.name == ".gitkeep":
                    continue
                if item.is_file():
                    try:
                        item.unlink()
                        pruned_count += 1
                    except Exception as e:
                        logger.error(f"Failed to purge {item}: {e}")
        
        # Clear engine in-memory caches if accessible
        try:
            from . import server_state
            if hasattr(server_state, "engine") and server_state.engine:
                engine = server_state.engine
                # Clear dictionaries if they exist
                for attr in ["preset_embeddings", "clone_embedding_cache", "mix_embedding_cache", 
                            "bgm_cache", "prompt_cache", "transcription_cache", 
                            "translation_cache", "video_audio_cache"]:
                    if hasattr(engine, attr):
                        getattr(engine, attr).clear()
                
                # Clear whisper model if lazy-loaded
                if hasattr(engine, "_whisper_model"):
                    engine._whisper_model = None
                
                logger.info("StorageManager: Engine in-memory caches purged.")
            
            # Clear CUDA cache if applicable
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as e:
            logger.error(f"Failed to clear engine/CUDA cache: {e}")

        # Also clear DSP caches
        global _eq_filter_cache
        _eq_filter_cache.clear()

        self.last_cleanup_time = time.time()
        self.total_pruned_count += pruned_count
        logger.info(f"StorageManager: Manual purge complete. Cleared {pruned_count} files.")
        return pruned_count

    def get_stats(self) -> dict:
        return {
            "last_cleanup": self.last_cleanup_time,
            "total_pruned": self.total_pruned_count,
            "retention_days": self.max_age_days
        }

class Profiler:
    """Context manager for profiling code blocks using cProfile."""
    def __init__(self, name: str):
        self.name = name
        import cProfile
        self.profiler = cProfile.Profile()

    def __enter__(self):
        self.profiler.enable()
        return self

    def __exit__(self, *args):
        self.profiler.disable()
        import pstats
        import io
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20) # Top 20 functions
        logger.info(f"--- Profiling Result: {self.name} ---\n{s.getvalue()}")

audit_manager = AuditManager()
resource_monitor = ResourceMonitor()
storage_manager = StorageManager()
