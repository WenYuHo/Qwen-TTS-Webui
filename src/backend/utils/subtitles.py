import datetime

def _fmt(seconds: float) -> str:
    """Format seconds into SRT timestamp (HH:MM:SS,mmm)."""
    td = datetime.timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def _fmt_vtt(seconds: float) -> str:
    """Format seconds into WebVTT timestamp (HH:MM:SS.mmm)."""
    return _fmt(seconds).replace(',', '.')

def generate_srt_from_segments(segments: list) -> str:
    """Generate SRT from Whisper-style segments with timestamps."""
    entries = []
    for i, seg in enumerate(segments):
        start = _fmt(seg["start"])
        end = _fmt(seg["end"])
        text = seg["text"].strip()
        entries.append(f"{i+1}\n{start} --> {end}\n{text}\n")
    return "\n".join(entries)

def generate_vtt_from_segments(segments: list) -> str:
    """Generate WebVTT from segments."""
    header = "WEBVTT\n\n"
    entries = []
    for i, seg in enumerate(segments):
        start = _fmt_vtt(seg["start"])
        end = _fmt_vtt(seg["end"])
        entries.append(f"{start} --> {end}\n{seg['text'].strip()}\n")
    return header + "\n".join(entries)
