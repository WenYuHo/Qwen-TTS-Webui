import json
import re
from typing import List, Dict, Any

# Viseme mapping (Rhubarb style)
# X: idle, A: closed, B: slightly open, C: open, D: wide open, 
# E: rounded, F: stretched, G: teeth on lip, H: tongue up
VISEME_MAP = {
    'a': 'D', 'e': 'C', 'i': 'F', 'o': 'E', 'u': 'E',
    'm': 'A', 'b': 'A', 'p': 'A',
    'f': 'G', 'v': 'G',
    'l': 'H',
    's': 'B', 'z': 'B', 'sh': 'B', 'ch': 'B', 'j': 'B',
    'k': 'B', 'g': 'B',
    't': 'B', 'd': 'B', 'n': 'B'
}

def text_to_visemes(text: str, language: str = "en") -> List[str]:
    """Simple heuristic G2V (Grapheme-to-Viseme) converter."""
    text = text.lower()
    visemes = []
    
    if language == "zh":
        # Simplified Chinese heuristic (focus on vowels)
        # In a real app, we'd use pypinyin
        for char in text:
            if re.match(r'[\u4e00-\u9fa5]', char):
                visemes.extend(['B', 'D']) # Simple open-close for each hanzi
            elif char.isspace():
                visemes.append('X')
    else:
        # English heuristic
        i = 0
        while i < len(text):
            char = text[i]
            if char.isspace() or char in ".,!?":
                visemes.append('X')
                i += 1
                continue
                
            # Check for multi-char phonemes
            found = False
            for length in [2, 1]:
                chunk = text[i:i+length]
                if chunk in VISEME_MAP:
                    visemes.append(VISEME_MAP[chunk])
                    i += length
                    found = True
                    break
            
            if not found:
                # Fallback to B for consonants, D for unknown vowels
                if char in "aeiouy":
                    visemes.append('D')
                elif char.isalpha():
                    visemes.append('B')
                i += 1
                
    return visemes

def generate_viseme_timestamps(text: str, duration: float, language: str = "en") -> List[Dict[str, Any]]:
    """Generates a list of visemes with start/end timestamps."""
    visemes = text_to_visemes(text, language)
    if not visemes:
        return [{"start": 0, "end": duration, "value": "X"}]
        
    # Heuristic: Distribute visemes evenly over duration, 
    # but give 'X' (silence) less weight if possible.
    # For a real implementation, we'd use forced alignment.
    
    # Remove consecutive identical visemes to simplify
    collapsed = []
    if visemes:
        collapsed.append(visemes[0])
        for v in visemes[1:]:
            if v != collapsed[-1]:
                collapsed.append(v)
    
    unit_duration = duration / len(collapsed)
    
    timestamps = []
    for i, v in enumerate(collapsed):
        timestamps.append({
            "start": round(i * unit_duration, 3),
            "end": round((i + 1) * unit_duration, 3),
            "value": v
        })
        
    # Ensure the last one hits the end exactly
    if timestamps:
        timestamps[-1]["end"] = round(duration, 3)
        
    return timestamps

def export_lip_sync_json(text: str, duration: float, language: str = "en") -> str:
    """Returns a JSON string of lip-sync data."""
    data = {
        "metadata": {
            "duration": duration,
            "text": text,
            "language": language
        },
        "mouthCues": generate_viseme_timestamps(text, duration, language)
    }
    return json.dumps(data, indent=2)
