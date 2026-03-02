import re
from pathlib import Path

def sync_tech_stack():
    req_path = Path("requirements.txt")
    tech_stack_path = Path("conductor/tech-stack.md")
    
    if not req_path.exists() or not tech_stack_path.exists():
        print("Required files missing.")
        return

    with open(req_path, "r") as f:
        reqs = [line.split("==")[0].strip() for line in f if line.strip() and not line.startswith("#")]

    # Categorize
    categories = {
        "API": ["fastapi", "uvicorn", "python-multipart"],
        "Audio": ["soundfile", "numpy", "pydub", "librosa", "scipy", "torchaudio"],
        "AI/ML": ["torch", "transformers", "accelerate", "einops", "onnxruntime", "openai-whisper"],
        "Video": ["ltx-pipelines", "diffusers", "opencv-python", "moviepy", "Pillow"],
        "Utils": ["python-dotenv", "psutil", "huggingface_hub", "deep-translator", "beautifulsoup4", "tqdm"],
        "Testing": ["pytest", "pytest-asyncio", "httpx"]
    }

    output_lines = []
    for cat, libs in categories.items():
        present = [l for l in libs if l in reqs]
        if present:
            output_lines.append(f"- **{cat}:** {', '.join(present)}")

    new_content = "
".join(output_lines)
    
    with open(tech_stack_path, "r") as f:
        content = f.read()

    pattern = r"<!-- DEPENDENCIES_START -->.*?<!-- DEPENDENCIES_END -->"
    replacement = f"<!-- DEPENDENCIES_START -->
{new_content}
<!-- DEPENDENCIES_END -->"
    
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(tech_stack_path, "w") as f:
        f.write(updated_content)
    
    print("Tech stack documentation synchronized with requirements.txt")

if __name__ == "__main__":
    sync_tech_stack()
