# Task Queue: Autonomous Improvement

## Prioritized Backlog

### Tier 1: Performance & UX
1. [ ] **Streaming TTS:** Refactor the synthesis engine to support Dual-Track streaming for ~100ms latency previews.
2. [ ] **LTX-Video Advanced Tuning:** Add sliders for Guidance Scale, Inference Steps, and Seed selection in the Video Generation panel.

### Tier 2: Governance & Safety
1. [ ] **Watermarking:** Integrate AI watermarking (audible or metadata) for compliance with transparency standards.

## Completed (Mar 2026 Refactor)
- [x] Implement **Phoneme Editor** UI and backend for custom pronunciation fixes.
- [x] Implement **Subtitle Generation** (.srt) for narrated videos.
- [x] Implement **Instruction Brackets** support for emotional cues in scripts.
- [x] Document the `TaskManager` class in `src/backend/task_manager.py`.
- [x] Add type hints to `src/backend/podcast_engine.py` methods.
- [x] Standardize error handling in `src/backend/api/voices.py` using centralized logger.
- [x] Refactor `src/static/app.js` into modular ES files (`task_manager.js`, `assets.js`, `system.js`, `production.js`).
- [x] Update `conductor/product.md` with "Technoid Brutalist" design direction and LTX features.
- [x] Create missing `README.md` for `src/backend/qwen_tts/core/`.
- [x] Implement Unified Model Inventory UI (Qwen + LTX).
- [x] Integrate Video Generation (LTX) into Project Studio workflow.
- [x] Enhance `setup_env.bat` with CUDA detection.
- [x] Cleaned stale logs, projects, and dummy uploads.

## Awaiting Human Feedback
- Should we move `setup_env.sh` and `start.sh` into a `bin/` or `scripts/` folder? (Standard practice vs ease of use).
