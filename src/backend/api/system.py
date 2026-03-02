import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..utils import phoneme_manager
from ..config import PROJECTS_DIR

router = APIRouter(prefix="/api/system", tags=["system"])

SETTINGS_FILE = PROJECTS_DIR / "settings.json"

class PhonemeOverride(BaseModel):
    word: str
    phonetic: str

class SystemSettings(BaseModel):
    watermark_audio: bool = True
    watermark_video: bool = True

def load_settings() -> SystemSettings:
    if not SETTINGS_FILE.exists():
        return SystemSettings()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return SystemSettings(**data)
    except Exception:
        return SystemSettings()

def save_settings(settings: SystemSettings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        f.write(settings.model_dump_json(indent=2))

# Initial load
_settings = load_settings()

@router.get("/settings")
async def get_settings():
    return _settings

@router.post("/settings")
async def update_settings(settings: SystemSettings):
    global _settings
    _settings = settings
    save_settings(_settings)
    return {"status": "ok", "settings": _settings}

@router.get("/audit")
async def get_audit_log():
    from ..utils import audit_manager
    return {"log": audit_manager.get_log()}

@router.get("/stats")
async def get_system_stats():
    from ..utils import resource_monitor
    return resource_monitor.get_stats()

@router.post("/benchmark")
async def run_benchmark():
    """Runs a profiled synthesis task and returns the performance breakdown."""
    import io
    import pstats
    from ..utils import Profiler
    from .. import server_state
    
    # Sample data for benchmarking
    text = "This is a performance benchmark synthesis for the Qwen TTS engine."
    profile = {"type": "preset", "value": "Ryan"}
    
    try:
        with Profiler("Engine Benchmark") as p:
            # Run a small synthesis
            server_state.engine.generate_segment(text, profile)
            
        # Extract the results from the profiler internal StringIO or re-run logic
        # For simplicity in this endpoint, we'll re-capture manually to return as JSON
        import cProfile
        pr = cProfile.Profile()
        pr.enable()
        server_state.engine.generate_segment(text, profile)
        pr.disable()
        
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(30) # Return top 30
        
        return {"status": "ok", "output": s.getvalue()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")

@router.get("/phonemes")
async def get_phonemes():
    return {"overrides": phoneme_manager.overrides}

@router.post("/phonemes/bulk")
async def bulk_add_phonemes(overrides: Dict[str, str]):
    try:
        new_overrides = phoneme_manager.overrides.copy()
        new_overrides.update(overrides)
        phoneme_manager.save(new_overrides)
        return {"status": "ok", "overrides": phoneme_manager.overrides}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/phonemes")
async def add_phoneme(override: PhonemeOverride):
    try:
        overrides = phoneme_manager.overrides.copy()
        overrides[override.word] = override.phonetic
        phoneme_manager.save(overrides)
        return {"status": "ok", "overrides": phoneme_manager.overrides}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/phonemes/{word}")
async def delete_phoneme(word: str):
    try:
        overrides = phoneme_manager.overrides.copy()
        if word in overrides:
            del overrides[word]
            phoneme_manager.save(overrides)
        return {"status": "ok", "overrides": phoneme_manager.overrides}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
