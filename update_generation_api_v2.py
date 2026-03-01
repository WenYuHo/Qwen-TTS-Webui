import sys

with open('src/backend/api/generation.py', 'r') as f:
    content = f.read()

content = content.replace(
    'result = server_state.engine.generate_podcast(script_data, profiles=profiles_map, bgm_mood=request_data.bgm_mood)',
    'result = server_state.engine.generate_podcast(script_data, profiles=profiles_map, bgm_mood=request_data.bgm_mood, ducking_level=request_data.ducking_level or 0.0)'
)

with open('src/backend/api/generation.py', 'w') as f:
    f.write(content)
