import datetime
import re
from pathlib import Path

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

def generate_srt(scenes: list, scene_durations: list) -> str:
    """Generate SRT subtitle content from multi-scene data."""
    entries = []
    offset = 0.0
    for i, (scene, duration) in enumerate(zip(scenes, scene_durations)):
        text = getattr(scene, 'narration_text', str(scene))
        # Split into sentences for finer-grained subtitles
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if not sentences or (len(sentences) == 1 and not sentences[0]):
             sentences = [text]
             
        sentence_duration = duration / max(len(sentences), 1)
        for j, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            start = offset + j * sentence_duration
            end = start + sentence_duration
            entries.append(f"{len(entries)+1}\n{_fmt(start)} --> {_fmt(end)}\n{sentence.strip()}\n")
        offset += duration
    return "\n".join(entries)

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

def _parse_srt_to_clips(srt_content, video_size, position="bottom", font_size=24):
    """Parse SRT content and return a list of MoviePy TextClips."""
    from moviepy.editor import TextClip
    
    w, h = video_size
    clips = []
    
    # Simple SRT parser
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)"
    matches = re.finditer(pattern, srt_content, re.DOTALL)
    
    for match in matches:
        start_time_str = match.group(2).replace(',', '.')
        end_time_str = match.group(3).replace(',', '.')
        text = match.group(4).strip().replace('\n', ' ')
        
        # Convert HH:MM:SS.mmm to seconds
        def to_sec(s):
            hrs, mins, secs = s.split(':')
            return int(hrs) * 3600 + int(mins) * 60 + float(secs)
        
        start = to_sec(start_time_str)
        end = to_sec(end_time_str)
        
        # Create TextClip
        try:
            txt_clip = TextClip(
                text, 
                fontsize=font_size, 
                color='white', 
                font='Arial',
                stroke_color='black', 
                stroke_width=1,
                method='caption',
                size=(w * 0.8, None)
            ).set_start(start).set_end(end)
            
            # Set position
            if position == "bottom":
                txt_clip = txt_clip.set_position(('center', h * 0.8))
            elif position == "top":
                txt_clip = txt_clip.set_position(('center', h * 0.1))
            elif position == "center":
                txt_clip = txt_clip.set_position(('center', 'center'))
                
            clips.append(txt_clip)
        except Exception as e:
            # Fallback if ImageMagick is missing or font fails
            from ..config import logger
            logger.error(f"Failed to create TextClip for subtitle: {e}")
            continue
            
    return clips

def burn_subtitles(video_path: str, srt_path: str, position: str = "bottom",
                   font_size: int = 24, output_path: str = None) -> str:
    """Burn SRT subtitles into video using MoviePy TextClip."""
    from moviepy.editor import VideoFileClip, CompositeVideoClip
    from ..config import logger

    logger.info(f"Burning subtitles from {srt_path} into {video_path}")
    
    video = VideoFileClip(video_path)
    # Parse SRT
    with open(srt_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()

    subtitle_clips = _parse_srt_to_clips(srt_content, video.size, position, font_size)
    if not subtitle_clips:
        logger.warning("No subtitle clips were generated. Check if ImageMagick is installed.")
        video.close()
        return video_path

    final = CompositeVideoClip([video] + subtitle_clips)

    out = output_path or video_path.replace('.mp4', '_subtitled.mp4')
    final.write_videofile(out, codec='libx264', audio_codec='aac', logger=None)
    
    # Cleanup
    video.close()
    for clip in subtitle_clips:
        clip.close()
        
    return out
