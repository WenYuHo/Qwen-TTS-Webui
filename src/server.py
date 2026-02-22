import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.api import voices, generation, projects, tasks, models
from backend.server_state import engine
from backend.config import logger

app = FastAPI(title="Qwen-TTS Studio")

# Include routers
app.include_router(voices.router)
app.include_router(generation.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(models.router)

# Aliases and root level endpoints
@app.get("/api/health")
async def health_check():
    return engine.get_system_status()

@app.get("/api/speakers")
async def get_speakers_alias():
    # Return same as /api/voice/speakers
    return await voices.get_speakers()

# Static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(static_dir / "index.html")

if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    logger.info("Starting Qwen-TTS Studio server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
