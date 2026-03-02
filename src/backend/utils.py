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
                # Simple GPU usage via torch
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

audit_manager = AuditManager()
resource_monitor = ResourceMonitor()
