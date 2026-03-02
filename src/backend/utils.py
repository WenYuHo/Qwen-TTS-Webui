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
    """Logs system-wide AI generation events for transparency and tracking."""
    def __init__(self):
        self.file_path = PROJECTS_DIR / "audit.json"
        self.lock = threading.Lock()

    def log_event(self, event_type: str, metadata: dict, status: str):
        """Append a new event record to the audit log."""
        event = {
            "timestamp": time.time(),
            "type": event_type,
            "status": status,
            "metadata": self._sanitize_metadata(metadata)
        }
        
        with self.lock:
            log = self._load()
            log.append(event)
            # Keep only last 1000 events to prevent file bloat
            if len(log) > 1000:
                log = log[-1000:]
            self._save(log)

    def _sanitize_metadata(self, metadata: dict) -> dict:
        """Removes sensitive or overly large data from log metadata."""
        sanitized = metadata.copy()
        # Remove raw results or large lists
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

audit_manager = AuditManager()
