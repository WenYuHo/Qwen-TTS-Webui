# Agent Memory: Qwen-TTS Podcast Studio

## System Overview
- **Core Stack:** FastAPI (Backend), Vanilla JS/CSS (Frontend), PyTorch (ML), Pydub/Soundfile (Audio).
- **Primary Purpose:** Professional web suite for Qwen-TTS voice synthesis, cloning, and podcast production.
- **Key Directories:**
  - `src/backend/`: Logic, API routers, and engine.
  - `src/static/`: Frontend assets (app.js, shared.js, style.css).
  - `conductor/`: High-level project documentation and tracks.
  - `projects/`: User project JSONs and voice library.
  - `shared_assets/`: BGM and SFX files.

## Codebase Insights
- **Visual Style:** Currently transitioning/conflicted between "Classic Studio" (as per `product-guidelines.md`) and "Technoid Brutalist" (as per `AGENTS.md` and `palette.md`). The Brutalist style uses Onyx (#080808) and Volt (#ccff00) with 2px sharp borders.
- **Security:** Strict path traversal protection in `PodcastEngine._resolve_paths`. Uses `Path.is_relative_to`.
- **Performance:** Multi-layered caching (BGM, embeddings, transcription, translation). LRU model cache in `ModelManager`.
- **Entry Points:** `src/server.py` (Backend), `index.html` (Frontend).
- **Dependency Management:** Private `.venv` created via `setup_env.sh`.

## Maintenance Notes
- **Stale Scripts:** Many `update_*.py` and `verify_*.py` scripts exist at the root level from past iterations.
- **Agent System:** Instruction files located in `.jules/`.
- **Workflow:** Supports direct push to main (Option 3) when requested.

## Human Notes
*Maintainer: Add specific instructions or "traps to avoid" here.*
- (Placeholder)
