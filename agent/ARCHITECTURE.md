# Current Architecture State

*   **Frontend**: Vanilla JS/CSS (Technoid Brutalist UI). Heavily modularized (`src/static/*.js`).
*   **Backend**: Python FastAPI (`src/backend/api/`). Fully async architecture using `BackgroundTasks`.
*   **Engine**: `PodcastEngine` (`src/backend/podcast_engine.py`) coordinates audio synthesis, mixing, and BGM ducking.
*   **ML Integration**: Direct `transformers` pipeline for Qwen-TTS; `LTX-Video` for generation.
*   **Dependencies**: Uses system binaries (`ffmpeg`, `sox`) localized to `/bin`.
