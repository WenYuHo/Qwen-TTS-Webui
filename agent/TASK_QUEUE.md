# Task Queue: Autonomous Improvement

## Prioritized Backlog

### Tier 1: UI & Video
1. [ ] **Video Preview Modal:** Create a specialized modal for playing generated narrated videos with subtitle overlay support.
2. [ ] **UI Style Unification:** Apply "Technoid Brutalist" styles to the Voice Studio, Asset Library, and Project Studio views.

### Tier 2: Governance & Automation
1. [ ] **Documentation:** Add a `CONTRIBUTING.md` file explaining the Conductor framework and modular JS structure.
2. [ ] **Unit Test Expansion:** Create automated tests for the new `AudioPostProcessor`, `AuditManager`, and `StorageManager`.

## Completed (Mar 2026 Refactor)
- [x] Implement **Project Search** (Filter) for voices, assets, and projects.
- [x] Implement **Auto-Cleanup** background thread for stale files (7-day retention).
- [x] Implement **Resource Monitoring** (CPU/RAM/GPU) in System Manager.
- [x] Apply **Technoid Brutalist Polish** to the System view UI.
- [x] Implement **Generation Audit Log** (audit.json) for transparency.
- [x] Implement **Audio Effects** (EQ & Reverb) for atmospheric polish.
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
