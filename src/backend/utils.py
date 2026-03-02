import io
import json
import soundfile as sf
import numpy as np
from pathlib import Path
from .config import PROJECTS_DIR

def numpy_to_wav_bytes(waveform, sample_rate):
    """Converts a numpy waveform to a WAV-formatted BytesIO object."""
    # Ensure waveform is float32
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
        # Simple word-based replacement
        for word, phonetic in self.overrides.items():
            # Use case-insensitive replacement with word boundaries
            import re
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            modified_text = pattern.sub(phonetic, modified_text)
        return modified_text

phoneme_manager = PhonemeManager()

class AudioPostProcessor:
    # ... (existing code)

class AuditManager:
    # ... (existing code)

class ResourceMonitor:
    # ... (existing code)

class StorageManager:
    """Manages disk space by periodically pruning stale generation artifacts."""
    def __init__(self, max_age_days: int = 7):
        from .config import PROJECTS_DIR, BASE_DIR
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
        # Run every 24 hours
        while not self._stop_event.wait(86400):
            self.prune()

    def prune(self):
        """Scan target directories and delete old files."""
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

audit_manager = AuditManager()
resource_monitor = ResourceMonitor()
storage_manager = StorageManager()
