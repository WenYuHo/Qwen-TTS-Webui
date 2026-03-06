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
4. **Memory-First Workflow:** Agents MUST read this file, `TASK_QUEUE.md`, and the active track before writing any code.

## Active Tracks
- **Sound Generation Performance & Quality** (`conductor/track-sound-generation.md`): 5-phase plan. Phases 1 & 2 implemented (Mar 2026). Phases 3-5 next.
- **Dubbing & Voice Conversion Pipeline** (`conductor/track-dubbing-pipeline.md`): 3 phases — dubbing hardening, S2S enhancement, multi-speaker dubbing.
- **Production Workflow & Export** (`conductor/track-production-workflow.md`): 4 phases — editor power features, multi-format export, templates, timeline view.
- **Voice Library & Expressive Control** (`conductor/track-voice-library.md`): 3 phases — library management, emotion/rate controls, quality insights.
- **Narrated Video Production** (`conductor/track-narrated-video.md`): 3 phases — multi-scene narrated videos (Qwen+LTX), audio-video sync, batch rendering.
- **Testing & Reliability** (`conductor/track-testing-reliability.md`): 4 phases — coverage gaps, module tests, E2E/browser, CI/CD.
- **Multilingual & Accessibility** (`conductor/track-multilingual-accessibility.md`): 3 phases — 10-language support, i18n, WCAG accessibility.
- **Autonomous Improvement** (`conductor/track-autonomous-improvement.md`): Standing improvement loop.
- **📘 Track Writing Guide** (`conductor/track-writing-guide.md`): Reference doc for writing detailed tracks — templates, rules, checklists.

## Recent Changes (Mar 2026)
- **Voice Preview Overhaul:** Replaced generic preview text with curated phonetically-diverse sentences. Added custom preview text input. Added `instruct` hint for clarity.
- **ICL Cloning Mode:** Voice cloning now supports `ref_text` for In-Context Learning mode, producing dramatically better voice quality. Schema, engine, and frontend all updated.
- **Files Changed:** `schemas.py`, `voices.py`, `podcast_engine.py`, `index.html`, `voicelab.js`, `shared.js`.
