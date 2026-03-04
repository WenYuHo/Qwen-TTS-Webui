# Agent Memory: Qwen-TTS Podcast Studio

> **MASTER FRAMEWORK:** This project uses the **Conductor Framework** located in `/conductor`.
> **SOURCE OF TRUTH:** Always follow [conductor/index.md](/conductor/index.md) for workflows and style.

## Current Project State (Refactored Mar 2026)
- **Environment:** Verified and healthy. Automated FFmpeg/SoX setup implemented. Virtual environment updated with core ML dependencies.
- **Root Cleanup:** One-off scripts moved to `/tools`. Redundant `AGENTS.md` and `high-autonomy-framework-v3/` staging deleted.
- **Environment:** Unified `studio.bat` and `studio.sh` (replaces `setup_env.bat` and `start.bat`).
- **Core Stack:** FastAPI (Backend), Vanilla JS/CSS (Frontend), PyTorch (ML).
- **Video Generation:** LTX-2 (19B) and LTX-Video (2B/13B) integrated via `ltx_video_engine.py`.
- **Documentation:** Root-level `agent.md` added as the primary entry point for AI agents.

## Folder Structure
- `/src/backend`: FastAPI server, business logic, and ML engines.
- `/src/static`: Frontend assets (modular JS, CSS, HTML).
- `/conductor`: Project governance, product definition, and tech stack.
- `/agent`: Agent-specific state (Memory, Task Queue, Logs).
- `/tools`: Utility scripts for maintenance and setup.
- `/tests`: Comprehensive test suite (Unit, Integration, E2E).
- `/projects`: User-generated project data.
- `/uploads`: Temporary user uploads.

## Core Philosophical Tenets
1. **Technoid Brutalism:** High-contrast, efficient, and direct UI/UX.
2. **Autonomous Improvement:** The system is designed to be self-healing and incrementally improved by agents.
3. **Stream-First Architecture:** Prioritize low-latency audio/video streaming for a responsive feel.
