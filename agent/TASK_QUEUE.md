# Task Queue: Autonomous Improvement

## Prioritized Backlog

### Tier 1: Performance & Reliability
1. [ ] **True Streaming:** Refactor `PodcastEngine` to support generator-based streaming for real-time synthesis during long script production.
2. [ ] **Model Checkpoint Tests:** Add a diagnostic test to verify that downloaded LTX checkpoints are valid safetensors/pth files.

### Tier 2: Governance & Search
1. [ ] **Scene Search AI:** Upgrade keyword-based search to use a small LLM or embedding-based search for better LTX-Video prompt suggestions.
2. [ ] **Error UI:** Create a specialized "Error Boundary" component in the UI to handle and display synthesis failures gracefully.

## Completed (Mar 2026 Refactor)
- [x] Create **automated unit tests** for `AudioPostProcessor`, `AuditManager`, and `StorageManager`.
- [x] Create **CONTRIBUTING.md** with framework and design system guidelines.
- [x] Apply **Technoid Brutalist UI Unification** to all views.
- [x] Implement **Video Preview Modal** with integrated subtitle overlay support.
- [x] Implement **Project Search** (Filter) for voices, assets, and projects.
- [x] Implement **Auto-Cleanup** background thread for stale files.
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
