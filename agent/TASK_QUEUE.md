# Task Queue: Autonomous Improvement

## Prioritized Backlog

### Tier 1: System Refinement
1. [ ] **Phoneme Editor Refinement:** Add a "Bulk Import" feature for phonetic dictionaries.
2. [ ] **Persistent Settings:** Refactor `api/system.py` to persist `SystemSettings` to a JSON file.

### Tier 2: Performance & UX
1. [ ] Refactor the synthesis engine to support true generator-based streaming for even lower latency.
2. [ ] Implement "Scene Search" for LTX-Video to suggest prompts based on script keywords.

## Completed (Mar 2026 Refactor)
- [x] Implement **AI Watermarking** (Audible & Visible) for AI-generated content.
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
