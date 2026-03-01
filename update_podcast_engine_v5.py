import sys
import re

with open('src/backend/podcast_engine.py', 'r') as f:
    content = f.read()

# 1. Update signature
content = content.replace(
    'def generate_podcast(self, script: List[Dict[str, Any]], profiles: Dict[str, Dict[str, Any]], bgm_mood: Optional[str] = None) -> Dict[str, Any]:',
    'def generate_podcast(self, script: List[Dict[str, Any]], profiles: Dict[str, Dict[str, Any]], bgm_mood: Optional[str] = None, ducking_level: float = 0.0) -> Dict[str, Any]:'
)

# 2. Update BGM logic
bgm_logic = """
        if bgm_mood:
            try:
                from .config import SHARED_ASSETS_DIR, BASE_DIR
                bgm_file = None

                # 1. Check shared assets
                shared_path = SHARED_ASSETS_DIR / bgm_mood
                if shared_path.exists():
                    bgm_file = shared_path
                else:
                    # 2. Fallback to preset bgm/ folder
                    bgm_full_path = (Path(BASE_DIR) / "bgm" / f"{bgm_mood}.mp3").resolve()
                    if bgm_full_path.exists():
                        bgm_file = bgm_full_path

                if bgm_file:
                    bgm_segment = AudioSegment.from_file(bgm_file) - 20
                    if len(bgm_segment) < len(final_mix):
                        loops = int(len(final_mix) / len(bgm_segment)) + 1
                        bgm_segment = bgm_segment * loops
                    bgm_segment = bgm_segment[:len(final_mix)]

                    if ducking_level > 0:
                        ducking_db = - (ducking_level * 25)
                        for seg in segments:
                            pos = seg["position"]
                            dur = len(seg["audio"])
                            if pos + dur > len(bgm_segment): continue

                            ducked_part = bgm_segment[pos:pos+dur] + ducking_db
                            bgm_segment = bgm_segment[:pos] + ducked_part + bgm_segment[pos+dur:]

                    final_mix = final_mix.overlay(bgm_segment)

            except Exception as e:
                logger.error(f"BGM mixing failed: {e}")
"""

# Replace the whole block from 'if bgm_mood:' to 'samples ='
pattern = r'if bgm_mood:.*?samples ='
content = re.sub(pattern, bgm_logic + '\n\n        samples =', content, flags=re.DOTALL)

with open('src/backend/podcast_engine.py', 'w') as f:
    f.write(content)
