# Qwen-TTS Studio - Agent Guide

This file contains instructions and information for AI agents working on this repository.

## Architecture Overview

The application is a FastAPI-based voice studio for Qwen-TTS. It follows a modular architecture:

- `src/server.py`: The entry point. Mounts routers and static files.
- `src/backend/api/`: Contains modular routers:
  - `voices.py`: Voice library management, upload, mix validation, and previews.
  - `generation.py`: All synthesis endpoints (TTS, S2S, Dubbing).
  - `projects.py`: Saving and loading multi-character studio projects.
  - `tasks.py`: Asynchronous task status and result polling.
  - `models.py`: Model inventory and downloader.
- `src/backend/podcast_engine.py`: The core logic that wraps the Qwen-TTS models.
- `src/backend/server_state.py`: Shared singleton instances of the engine and task manager.
- `src/static/`: Frontend assets.
  - `app.js`: Main application logic.
  - `shared.js`: Shared state and data persistence logic (unified with backend).

## Key Concepts

### Voice Persistence
User-designed voices are stored in `projects/voices.json`. The frontend `SpeakerStore` and backend `/api/voice/library` work together to ensure custom voices persist across sessions and are available in the Project Studio.

### Project Studio
Projects are stored as JSON in the `projects/` directory. They contain script blocks and associated voice profiles.

### Security: Path Traversal
When resolving file paths (e.g., for cloned voices or BGM), always use `PodcastEngine._resolve_path`. This method validates that files are within permitted directories (`uploads/` or `bgm/`) and prevents directory traversal attacks.

## Development & Testing

### Installation
Run `./setup_env.sh` (Linux/macOS) or `setup_env.bat` (Windows) to set up the environment.

### Running the Server
Run `./start.sh` or `python3 src/server.py`. The server runs on port 8080 by default.

### Running Tests
- Unit Tests: `PYTHONPATH=src pytest tests/test_api.py tests/test_enhanced.py`
- Smoke Test: Run the server, then `python3 tests/smoke_test.py`.

## Coding Conventions
- **Pydantic**: Use Pydantic V2 methods (`model_dump_json()`, `field_validator`).
- **Python**: Avoid semicolons. Use type hints for API models.
- **FastAPI**: Use `APIRouter` for all new endpoints. Avoid monolithic growth of `server.py`.

## Deployment
Logs are written to `logs/studio.log`. The `logs/` directory and `projects/*.json` are excluded from git to prevent leaking user data or runtime state.

## Workflow Automation
- **Option 3 (Direct Push to Main):** When explicitly requested by the user for faster iterations, Jules is authorized to push directly to the `main` branch.
- **Workflow Steps:**
  1. `git checkout main`
  2. `git pull origin main`
  3. `git merge <feature-branch>` (or `git add .` if working directly on main)
  4. `git commit -m "Jule automated update"`
  5. `git push origin main`
