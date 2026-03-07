# Codebase Map: Qwen-TTS Podcast Studio

An AI agent's guide to finding where things happen in this project.

## 🖥️ Frontend (`src/static/`)
**Philosophy**: Vanilla JS, ES6 Modules, strict separation of concerns.

*   `index.html`: The single-page application entry point. Contains all DOM structure.
*   `style.css`: All styling. **Technoid Brutalist** theme. No external CSS frameworks allowed.
*   `app.js`: Main initialization logic.
*   `system.js`: API communication (`fetch` wrappers), model loading, server status polling.
*   `assets.js`: Management of background music (BGM), sound effects, and project files.
*   `voicelab.js`: Voice cloning, voice generation previews, and managing the local voice library.
*   `production.js`: The timeline builder, script parsing, podcast generation triggers.
*   `dubbing.js`: Speech-to-Speech (S2S) and translation/dubbing interfaces.
*   `timeline.js`: The visual multi-track timeline rendering logic.
*   `task_manager.js`: UI for showing background server tasks (progress bars, status updates).
*   `shared.js`: Global state, utility functions, and shared types.
*   `ui_components.js`: Reusable UI DOM generator functions (modals, toasts).

## ⚙️ Backend API (`src/backend/api/`)
**Philosophy**: FastAPI, RESTful, asynchronous endpoints.

*   `schemas.py`: Pydantic models for *every* API request/response. Always check here for data shapes.
*   `system.py`: System status, model downloading, environment verification endpoints.
*   `projects.py`: Saving/loading `.json` project files and scripts.
*   `voices.py`: Calling VoiceLab, handling speaker profiles and voice arrays.
*   `generation.py`: Triggers for synthesizing single segments or entire podcasts.
*   `video.py`: Endpoints for LTX-Video and LTX-2 narrated video generation.
*   `assets.py`: Endpoints for uploading and listing BGM and sound effects.
*   `tasks.py`: Querying the state of background synthesis/generation tasks.

## 🧠 Core ML & Engines (`src/backend/`)
**Philosophy**: Heavy lifting, resource management, and external binary wrapping.

*   `podcast_engine.py`: **The Core Brain**. Orchestrates Qwen-TTS synthesis, BGM mixing, watermarking, spatial panning, and final export.
*   `task_manager.py`: Custom `asyncio` task queue. Prevents the FastAPI server from locking up during 30s+ inference runs.
*   `utils.py`: `AudioPostProcessor` (ACX compliance, normalization, silence padding), and script parsing utilities.
*   `config.py`: Environment variables, logging setup, and directory path resolution. Read this for any pathing questions.
*   `sox_shim.py` / `dub_logic.py` / `s2s_logic.py`: Wrappers around SoX and specialized logic for Voice Conversion.
*   `model_downloader.py` / `model_loader.py`: HuggingFace integration for pulling down Qwen and LTX models.

## 🧪 Testing (`tests/`)
**Philosophy**: Pytest, Asyncio, heavy mocking of ML models to keep tests fast.

*   `test_podcast_engine.py`: Validating the core audio creation logic.
*   `test_api_*.py`: Testing FastAPI endpoint responses.
*   `test_bolt_optimization.py`: Testing the caching and performance improvements of the engine.

## 📜 Conductor Framework (`conductor/`)
**Philosophy**: The project's product management and architectural governance.

*   `tech-stack.md`: Approved libraries and tools.
*   `product.md`: Product vision, target audience, aesthetic rules.
*   `workflow.md`: Strict TDD, commit, and AI-agent workflow rules.
*   `track-*.md`: Detailed roadmaps for specific features (e.g., dubbing, testing, video generation).
