import sys

with open('src/backend/api/generation.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "def validate_request(request: PodcastRequest):" in line:
        new_lines.append(line)
        new_lines.append("    if not request.script:\n")
        new_lines.append("        raise HTTPException(status_code=400, detail='Script is empty')\n")
        new_lines.append("    if len(request.script) > 100:\n")
        new_lines.append("        raise HTTPException(status_code=400, detail='Script too long')\n")
        new_lines.append("    for line in request.script:\n")
        new_lines.append("        if len(line.text) > 5000:\n")
        new_lines.append("            raise HTTPException(status_code=400, detail='Text too long')\n")
        skip = True
        continue
    if skip:
        if line.startswith("@router.post"):
            skip = False
            new_lines.append("\n")
            new_lines.append(line)
        continue
    new_lines.append(line)

with open('src/backend/api/generation.py', 'w') as f:
    f.writelines(new_lines)
