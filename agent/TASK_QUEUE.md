# Task Queue: Autonomous Improvement

## Prioritized Backlog

### Tier 1: Performance & Polish
1. [ ] **Audio Effects:** Add EQ and Reverb controls to the Production sidebar for atmospheric polish.
2. [ ] **UI Refinement:** Transition new cards to the "Technoid Brutalist" style (Volt accents, sharp shadows).

### Tier 2: Governance & Safety
1. [ ] **Audit Log:** Create a system-wide audit log for all generation tasks (TTS, Video, Dubbing) stored in `projects/audit.json`.
2. [ ] **Resource Monitoring:** Add a "CPU/GPU Load" indicator to the System view.

## Completed (Mar 2026 Refactor)
- [x] Implement **Scene Search** keyword-based prompt suggestions for LTX-Video.
- [x] Implement **Parallel Streaming Synthesis** with look-ahead for ultra-low latency.
- [x] Implement **Persistent System Settings** (settings.json).
- [x] Implement **Phoneme Editor Bulk Import** (JSON).
- [x] Implement **AI Watermarking** (Audible & Visible).
- [x] Implement **LTX-Video Advanced Tuning** (Guidance, Steps, Seed).
- [x] Implement **Dual-Track Streaming TTS** for low-latency (~100ms) previews.
- [x] Implement **Phoneme Editor** UI and backend for custom pronunciation fixes.
- [x] Implement **Subtitle Generation** (.srt) for narrated videos.
- [x] Implement **Instruction Brackets** support for emotional cues in scripts.
- [x] Document the `TaskManager` class in `src/backend/task_manager.py`.
- [x] Add type hints to `src/backend/podcast_engine.py` methods.
- [x] Standardize error handling in `src/backend/api/voices.py` using centralized logger.
- [x] Refactor `src/static/app.js` into modular ES files.
- [x] Update `conductor/product.md` with "Technoid Brutalist" design direction and LTX features.
- [x] Create missing `README.md` for `src/backend/qwen_tts/core/`.
- [x] Implement Unified Model Inventory UI (Qwen + LTX).
- [x] Integrate Video Generation (LTX) into Project Studio workflow.
- [x] Enhance `setup_env.bat` with CUDA detection.
- [x] Cleaned stale logs, projects, and dummy uploads.

## Awaiting Human Feedback
- Should we move `setup_env.sh` and `start.sh` into a `bin/` or `scripts/` folder? (Standard practice vs ease of use).
