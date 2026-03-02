# Agent Memory: Qwen-TTS Podcast Studio

> **MASTER FRAMEWORK:** This project uses the **Conductor Framework** located in `/conductor`.
> **SOURCE OF TRUTH:** Always follow [conductor/index.md](/conductor/index.md) for workflows and style.

## Current Project State (Refactored Mar 2026)
- **Root Cleanup:** One-off scripts moved to `/tools`. Redundant `AGENTS.md` deleted.
- **Environment:** Unified `setup_env.bat` and `start.bat`. Added `requirements_video.txt`.
- **Core Stack:** FastAPI (Backend), Vanilla JS/CSS (Frontend), PyTorch (ML).
- **Video Generation:** LTX-2 (19B) and LTX-Video (2B/13B) integrated via `ltx_video_engine.py`.
