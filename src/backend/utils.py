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
    """Applies atmospheric effects like EQ and Reverb to final waveforms."""
    
    @staticmethod
    def apply_eq(wav: np.ndarray, sr: int, preset: str = "flat") -> np.ndarray:
        """Applies a basic EQ filter based on presets."""
        if preset == "flat":
            return wav
            
        try:
            from scipy import signal
            # Simple 3-band EQ implementation using biquad filters
            if preset == "broadcast":
                # Boost bass and high-mids for that radio sound
                b, a = signal.butter(2, [80 / (sr/2), 5000 / (sr/2)], btype='bandpass')
                return signal.lfilter(b, a, wav) * 1.5
            elif preset == "warm":
                # Low-pass filter to remove harsh highs
                b, a = signal.butter(2, 3000 / (sr/2), btype='low')
                return signal.lfilter(b, a, wav)
            elif preset == "bright":
                # High-pass filter to emphasize clarity
                b, a = signal.butter(2, 1000 / (sr/2), btype='high')
                return signal.lfilter(b, a, wav)
        except ImportError:
            return wav
        return wav

    @staticmethod
    def apply_reverb(wav: np.ndarray, sr: int, intensity: float = 0.0) -> np.ndarray:
        """Applies a simple algorithmic reverb (echo-based)."""
        if intensity <= 0:
            return wav
            
        try:
            # Simple delay-based reverb (comb filter)
            delay_samples = int(0.05 * sr) # 50ms delay
            decay = intensity * 0.4
            
            out = wav.copy()
            # 3-tap simple echo for 'atmospheric' feel
            for i in range(1, 4):
                shift = delay_samples * i
                if shift < len(wav):
                    out[shift:] += wav[:-shift] * (decay ** i)
            
            # Normalize to avoid clipping
            max_amp = np.max(np.abs(out))
            if max_amp > 1.0:
                out /= max_amp
            return out
        except Exception:
            return wav
