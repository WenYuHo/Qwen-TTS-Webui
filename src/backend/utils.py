import io
import soundfile as sf
import numpy as np

def numpy_to_wav_bytes(waveform, sample_rate):
    """Converts a numpy waveform to a WAV-formatted BytesIO object."""
    # Ensure waveform is float32
    if waveform.dtype != np.float32:
        waveform = waveform.astype(np.float32)

    buffer = io.BytesIO()
    sf.write(buffer, waveform, sample_rate, format='WAV')
    buffer.seek(0)
    return buffer

def validate_safe_path(base_dir, relative_path):
    """Ensures the relative path does not escape the base directory."""
    import os
    from pathlib import Path
    base = Path(base_dir).resolve()
    full_path = (base / relative_path).resolve()
    if not full_path.is_relative_to(base):
        raise ValueError("Invalid path: path escapes base directory")
    return full_path
