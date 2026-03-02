import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.api import voices, generation, projects, tasks, models, assets, system
try:
    from backend.api import video
except ImportError:
    video = None

from backend import server_state
from backend.config import logger

app = FastAPI(title="Qwen-TTS Studio")

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Include routers
app.include_router(voices.router)
app.include_router(generation.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(models.router)
app.include_router(assets.router)
app.include_router(system.router)
if video:
    app.include_router(video.router)

# Health check
@app.get("/api/health")
async def health_check():
    return server_state.engine.get_system_status()

# Static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(static_dir / "index.html")

if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Start background cleanup
    from backend.utils import storage_manager
    storage_manager.start()
    
    logger.info("Starting Qwen-TTS Studio server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
