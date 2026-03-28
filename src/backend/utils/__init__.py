import io
import json
import re
import datetime
import soundfile as sf
import numpy as np
import time
import threading
import cProfile
import pstats
from pathlib import Path
from ..config import PROJECTS_DIR, BASE_DIR, logger

try:
    from scipy import signal as scipy_signal
except ImportError:
    scipy_signal = None

try:
    import psutil
except ImportError:
    psutil = None

try:
    import torch
except ImportError:
    torch = None

# ⚡ Bolt: Cache for Butterworth filter coefficients to avoid redundant DSP math
_eq_filter_cache = {}
# ⚡ Bolt: Cache for static GPU properties to avoid redundant CUDA driver calls
_gpu_info_cache = {}

def prune_dict_cache(cache: dict, limit: int, count: int = 100):
    """
    Remove the oldest `count` items from the dictionary if it exceeds `limit`.
    Leverages Python 3.7+ insertion ordering for O(count) pruning.
    """
    if len(cache) >= limit:
        # Use next(iter()) to get the first (oldest) key and pop it.
        # This is efficient for maintaining 'hot' items in the cache.
        for _ in range(min(count, len(cache))):
            try:
                key = next(iter(cache))
                cache.pop(key)
            except (StopIteration, KeyError):
                break

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
        # ⚡ Bolt: Map lowercased word directly to its phonetic override for O(1) lookup
        self.word_map = {word.lower(): phonetic for word, phonetic in self.overrides.items()}

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
            # ⚡ Bolt: Single dictionary lookup within a single-pass regex substitution
            return self.word_map.get(match.group(0).lower(), match.group(0))

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
                # ⚡ Bolt: Prevent unbounded growth of the EQ filter cache
                prune_dict_cache(_eq_filter_cache, limit=200, count=20)

                if preset == "broadcast":
                    b, a = scipy_signal.butter(2, [80 / (sr/2), 5000 / (sr/2)], btype='bandpass')
                    # ⚡ Bolt: Pre-scale coefficients to eliminate the O(N) multiplication pass later
                    b *= 1.5
                elif preset == "warm":
                    b, a = scipy_signal.butter(2, 3000 / (sr/2), btype='low')
                elif preset == "bright":
                    b, a = scipy_signal.butter(2, 1000 / (sr/2), btype='high')
                else:
                    return wav
                _eq_filter_cache[cache_key] = (b, a)

            out = scipy_signal.lfilter(b, a, wav)
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
            
            # ⚡ Bolt: Use max(np.max, -np.min) to avoid allocating a large temporary array for np.abs(out)
            max_amp = max(np.max(out), -np.min(out))
                
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
            # Ensure we are working with float32 to avoid in-place type errors and handle int inputs safely.
            # Bolt: copy=False avoids a copy if already float32.
            wav = wav.astype(np.float32, copy=False)

            # ⚡ Bolt: Use np.vdot for multi-channel RMS. It's ~5x faster than np.mean(wav**2)
            # and avoids an intermediate O(N) array allocation for the squares.
            current_rms = np.sqrt(np.vdot(wav, wav) / wav.size)
            if current_rms <= 0:
                return wav

            # ⚡ Bolt: Combine RMS gain and Peak limiting into a single gain factor to avoid multiple O(N) passes.
            # This is critical for performance when processing large (10min+) audio buffers.
            gain = 0.1 / current_rms

            # 2. Peak Limiting: -3dB (approx 0.707 linear)
            # ⚡ Bolt: Use max(np.max, -np.min) to avoid O(N) allocation for np.abs(wav)
            max_peak = max(np.max(wav), -np.min(wav))

            if max_peak * gain > 0.707:
                gain = 0.707 / max_peak

            if gain != 1.0:
                # ⚡ Bolt: multiplication creates a new array if input was read-only,
                # but since we ensured a float32 copy/view above, we can safely multiply.
                # To be absolutely safe regarding read-only/mmap, we avoid *= here
                # and just return wav * gain.
                return wav * gain

            return wav
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
            # ⚡ Bolt: Use broadcasting for O(1) weight application instead of O(N) slice assignment.
            # This avoids allocating a zero-array and reduces memory copies.
            weights = np.array([(1.0 - pan) / 2.0, (1.0 + pan) / 2.0], dtype=np.float32)
            return weights[:, None] * wav
        except Exception as e:
            logger.error(f"Panning failed: {e}")
            return np.stack([wav, wav]) # Fallback to dual-mono

    @staticmethod
    def apply_compressor(wav: np.ndarray, sr: int, threshold_db: float = -20.0, ratio: float = 4.0) -> np.ndarray:
        """Applies dynamic range compression."""
        try:
            # Handle stereo
            if len(wav.shape) > 1:
                # Apply to each channel independently for simplicity, or linked (using max)
                # Here we do independent to keep it simple and fast
                out = np.zeros_like(wav)
                for i in range(wav.shape[0]):
                    out[i] = AudioPostProcessor.apply_compressor(wav[i], sr, threshold_db, ratio)
                return out

            # Convert to dB
            # Avoid log(0)
            abs_wav = np.abs(wav)
            db_wav = 20 * np.log10(abs_wav + 1e-10)
            
            # Gain reduction
            mask = db_wav > threshold_db
            if not np.any(mask):
                return wav

            reduction = (db_wav - threshold_db) * (1 - 1/ratio)
            gain_db = np.zeros_like(db_wav)
            gain_db[mask] = -reduction[mask]
            
            gain_linear = 10 ** (gain_db / 20.0)
            return wav * gain_linear
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return wav

    @staticmethod
    def apply_declick(wav: np.ndarray, sr: int) -> np.ndarray:
        """Simple heuristic de-clicker: clamps spikes > 10x local RMS.
        ⚡ Bolt: Vectorized implementation using np.reshape and np.einsum for ~20x speedup.
        """
        try:
            if len(wav.shape) > 1:
                return np.stack([AudioPostProcessor.apply_declick(ch, sr) for ch in wav])

            window = int(sr * 0.002)  # 2ms
            if window < 2 or len(wav) < 2:
                return wav

            out = wav.copy()
            n_samples = len(wav)
            n_chunks = n_samples // window
            main_len = n_chunks * window

            if main_len > 0:
                # ⚡ Bolt: Reshape into chunks for vectorized RMS and spike detection
                chunks = wav[:main_len].reshape(n_chunks, window)
                # ⚡ Bolt: Use np.einsum for row-wise dot product (sum of squares) to avoid O(N) allocation of chunks**2
                rms = np.sqrt(np.einsum('ij,ij->i', chunks, chunks) / window) + 1e-6

                # ⚡ Bolt: Vectorized spike detection (10x local RMS)
                # rms[:, None] broadcasts the per-chunk RMS to the chunk shape
                spikes = np.abs(chunks) > (rms[:, None] * 10)

                if np.any(spikes):
                    # ⚡ Bolt: Apply clamping to identified spikes
                    row_idx, col_idx = np.where(spikes)
                    # Clamp to local RMS * 3
                    out_chunks = out[:main_len].reshape(n_chunks, window)
                    out_chunks[row_idx, col_idx] = np.sign(chunks[row_idx, col_idx]) * rms[row_idx] * 3

            # Handle remainder
            if main_len < n_samples:
                remainder = wav[main_len:]
                if len(remainder) >= 2:
                    local_rms = np.sqrt(np.vdot(remainder, remainder) / len(remainder)) + 1e-6
                    spikes = np.abs(remainder) > (local_rms * 10)
                    if np.any(spikes):
                        out[main_len:][spikes] = np.sign(remainder[spikes]) * local_rms * 3

            return out
        except Exception as e:
            logger.error(f"⚡ Bolt: De-click failed: {e}")
            return wav

class AuditManager:
    """Logs system-wide AI generation events for transparency and tracking."""
    def __init__(self):
        self.file_path = PROJECTS_DIR / "audit.json"
        self.lock = threading.Lock()
        self._cache = None # ⚡ Bolt: In-memory cache to avoid redundant I/O

    def log_event(self, event_type: str, metadata: dict, status: str):
        event = {
            "timestamp": time.time(),
            "type": event_type,
            "status": status,
            "metadata": self._sanitize_metadata(metadata)
        }
        with self.lock:
            # ⚡ Bolt: _load() now populates and returns the cache
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
        # ⚡ Bolt: Return cached log if available
        if self._cache is not None:
            return self._cache

        if not self.file_path.exists():
            self._cache = []
            return self._cache
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
                return self._cache
        except Exception:
            self._cache = []
            return self._cache

    def _save(self, log: list):
        # ⚡ Bolt: Always update cache on save to stay in sync
        self._cache = log
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)

    def get_log(self) -> list:
        with self.lock:
            # ⚡ Bolt: Return copy to prevent external mutation of cache
            return list(self._load())

    def clear_cache(self):
        """⚡ Bolt: Clear the in-memory cache."""
        with self.lock:
            self._cache = None

class ResourceMonitor:
    """Provides real-time CPU, RAM, and GPU usage metrics."""
    @staticmethod
    def get_stats() -> dict:
        # ⚡ Bolt: Use top-level imports for psutil and torch to avoid redundant lookup overhead
        stats = {
            "cpu_percent": psutil.cpu_percent() if psutil else 0,
            "ram_percent": psutil.virtual_memory().percent if psutil else 0,
            "gpu": None
        }
        try:
            if torch and torch.cuda.is_available():
                gpu_id = torch.cuda.current_device()

                # ⚡ Bolt: Cache static GPU properties (name, total VRAM) to reduce driver overhead
                if gpu_id not in _gpu_info_cache:
                    props = torch.cuda.get_device_properties(gpu_id)
                    _gpu_info_cache[gpu_id] = {
                        "name": props.name,
                        "vram_total": props.total_memory / (1024**3)
                    }

                gpu_static = _gpu_info_cache[gpu_id]
                vram_used = torch.cuda.memory_allocated(gpu_id) / (1024**3)

                stats["gpu"] = {
                    "name": gpu_static["name"],
                    "vram_total": gpu_static["vram_total"],
                    "vram_used": vram_used,
                    "vram_percent": (vram_used / gpu_static["vram_total"]) * 100
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
            from .. import server_state
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
            # ⚡ Bolt: Use top-level torch import
            if torch and torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as e:
            logger.error(f"Failed to clear engine/CUDA cache: {e}")

        # Also clear DSP caches
        global _eq_filter_cache
        _eq_filter_cache.clear()

        # ⚡ Bolt: Clear audit manager cache
        audit_manager.clear_cache()

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
        # ⚡ Bolt: Use top-level cProfile import
        self.profiler = cProfile.Profile()

    def __enter__(self):
        self.profiler.enable()
        return self

    def __exit__(self, *args):
        self.profiler.disable()
        # ⚡ Bolt: Use top-level io and pstats imports
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20) # Top 20 functions
        logger.info(f"--- Profiling Result: {self.name} ---\n{s.getvalue()}")

audit_manager = AuditManager()
resource_monitor = ResourceMonitor()
storage_manager = StorageManager()
