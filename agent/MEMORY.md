# Agent Memory & Context Map

> **MASTER FRAMEWORK:** This project uses the **Conductor Framework** located in `/conductor`.
> **SOURCE OF TRUTH:** Always follow [conductor/index.md](/conductor/index.md) for workflows and style.

## 🧠 What is this file?
This file is the "Memory Bank" for any AI coding assistant working on Qwen-TTS Podcast Studio. **It must be read at the start of every session.**
For a map of where code lives, see [CODEBASE_MAP.md](CODEBASE_MAP.md).
For a log of architectural choices, see [DECISIONS_LOG.md](DECISIONS_LOG.md).

---

## 🏗️ The Project: Qwen-TTS Podcast Studio (v2.1)
A high-fidelity audio production suite for multi-speaker podcasts, audio dramas, and narrated videos.

### Current Architecture State
*   **Frontend**: Vanilla JS/CSS (Technoid Brutalist UI). Heavily modularized (`src/static/*.js`).
*   **Backend**: Python FastAPI (`src/backend/api/`). Fully async architecture using `BackgroundTasks`.
*   **Engine**: `PodcastEngine` (`src/backend/podcast_engine.py`) coordinates audio synthesis, mixing, and BGM ducking.
*   **ML Integration**: Direct `transformers` pipeline for Qwen-TTS; `LTX-Video` for generation.
*   **Dependencies**: Uses system binaries (`ffmpeg`, `sox`) localized to `/bin`.

### 🚨 Critical Project Rules & Context
1.  **Do NOT use React/Vue/Tailwind:** The frontend is strictly Vanilla JS and custom CSS. Never introduce modern web frameworks.
2.  **Technoid Brutalist UI:** Use high-contrast Volt (#ccff00) on Onyx (#080808). UI should feel like industrial studio hardware.
3.  **Strict TDD:** Tests **must** be written (and fail) before application code is implemented. `pytest` is the runner. See `/conductor/workflow.md`.
4.  **No `print()` debugging in production:** Use the configured `logging` module in `config.py`.
5.  **Paths are Absolute:** The backend relies heavily on `pathlib.Path` relative to the project root. Never hardcode absolute disk paths or rely on `os.getcwd()` blindly.

---

## 📋 Active Development Tracks (Mar 2026)
*See `/conductor/tracks.md` for full index.*

1.  **Sound Generation Quality (`track-sound-generation.md`)**: Currently focusing on Phase 3/4 (Silence padding for ICL, Temperature presets, Auto-retry on low quality).
2.  **Dubbing & S2S (`track-dubbing-pipeline.md`)**: Hardening the Voice Conversion and Dubbing APIs.
3.  **Testing & Reliability (`track-testing-reliability.md`)**: Increasing unit test coverage, adding E2E browser tests. **Current priority: Bolt Optimizations.**
4.  **Production Workflow (`track-production-workflow.md`)**: Multi-format export, timeline views.

---

## ⚡ Recent Milestones & Context
*   **Bolt Optimizations**: We recently implemented "Bolt" optimizations in `podcast_engine.py` (e.g., caching audio watermark tones, lazy loading models, using `soundfile` instead of `librosa` for speed).
*   **ICL Cloning Overhaul**: Voice cloning uses `ref_text` for In-Context Learning (ICL) in Qwen-TTS. It works via concatenating the reference audio with the target text.
*   **LTX-Video Integrated**: Video generation is live via endpoints in `video.py`.
*   **ACX Mastering Added**: `utils.AudioPostProcessor` now contains ACX audio compliance normalization.

*To update this file: When major architectural changes occur or new tracks open, summarize them here to maintain the agent's cross-session awareness.*
