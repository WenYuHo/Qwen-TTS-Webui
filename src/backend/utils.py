import io
import json
import soundfile as sf
import numpy as np
import time
import threading
from pathlib import Path
from .config import PROJECTS_DIR, BASE_DIR, logger

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
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.overrides, f, indent=2, ensure_ascii=False)

    def apply(self, text: str) -> str:
        """Replace words in text with their phonetic equivalents."""
        if not self.overrides:
            return text
        modified_text = text
        for word, phonetic in self.overrides.items():
            import re
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            modified_text = pattern.sub(phonetic, modified_text)
        return modified_text

phoneme_manager = PhonemeManager()

class AudioPostProcessor:
    """Applies atmospheric effects like EQ and Reverb to final waveforms."""
    @staticmethod
    def apply_eq(wav: np.ndarray, sr: int, preset: str = "flat") -> np.ndarray:
        if preset == "flat":
            return wav
        try:
            from scipy import signal
            if preset == "broadcast":
                b, a = signal.butter(2, [80 / (sr/2), 5000 / (sr/2)], btype='bandpass')
                return signal.lfilter(b, a, wav) * 1.5
            elif preset == "warm":
                b, a = signal.butter(2, 3000 / (sr/2), btype='low')
                return signal.lfilter(b, a, wav)
            elif preset == "bright":
                b, a = signal.butter(2, 1000 / (sr/2), btype='high')
                return signal.lfilter(b, a, wav)
        except Exception:
            return wav
        return wav

    @staticmethod
    def apply_reverb(wav: np.ndarray, sr: int, intensity: float = 0.0) -> np.ndarray:
        if intensity <= 0:
            return wav
        try:
            delay_samples = int(0.05 * sr)
            decay = intensity * 0.4
            out = wav.copy()
            for i in range(1, 4):
                shift = delay_samples * i
                if shift < len(wav):
                    out[shift:] += wav[:-shift] * (decay ** i)
            max_amp = np.max(np.abs(out))
            if max_amp > 1.0:
                out /= max_amp
            return out
        except Exception:
            return wav

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
                if item.is_file():
                    try:
                        stat = item.stat()
                        if now - stat.st_mtime > max_age_seconds:
                            item.unlink()
                            pruned_count += 1
                    except Exception as e:
                        logger.error(f"Failed to prune {item}: {e}")
        if pruned_count > 0:
            logger.info(f"StorageManager: Pruned {pruned_count} stale files.")

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
