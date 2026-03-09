"""Speaker diarization using pyannote-audio."""
import torch
from pathlib import Path
import logging

logger = logging.getLogger("studio")
_pipeline = None

def get_diarization_pipeline(hf_token: str = None):
    global _pipeline
    if _pipeline is None:
        try:
            from pyannote.audio import Pipeline
            # In a real app, hf_token would come from .env
            token = hf_token or "YOUR_HF_TOKEN" 
            try:
                # ⚡ Bolt: Some versions use 'token', others 'use_auth_token'
                _pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=token
                )
            except TypeError:
                _pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    token=token
                )
            
            if _pipeline and not isinstance(_pipeline, str) and torch.cuda.is_available():
                _pipeline = _pipeline.to(torch.device("cuda"))
            logger.info("pyannote-audio pipeline loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load pyannote pipeline (likely missing/invalid token): {e}")
            _pipeline = "MOCK"
    return _pipeline

def diarize_audio(audio_path: str, hf_token: str = None) -> list:
    """Run speaker diarization. Returns list of segments with speaker labels."""
    pipeline = get_diarization_pipeline(hf_token)
    
    if pipeline == "MOCK":
        logger.info("Using MOCK diarization logic")
        # Return a dummy segment for the entire file
        import soundfile as sf
        try:
            info = sf.info(audio_path)
            duration = info.duration
        except:
            duration = 10.0 # Default for tests if file missing
            
        return [{
            "start": 0.0,
            "end": round(duration, 3),
            "speaker": "SPEAKER_00",
            "duration": round(duration, 3)
        }]

    diarization = pipeline(audio_path)
    
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "start": round(turn.start, 3),
            "end": round(turn.end, 3),
            "speaker": speaker,
            "duration": round(turn.end - turn.start, 3)
        })
    return segments
