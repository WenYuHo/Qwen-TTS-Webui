# Task Queue: Autonomous Improvement

## Prioritized Backlog

### Tier 1: Intelligence & Search
1. [ ] **Scene Search AI Upgrade:** Upgrade the keyword-based search to use a small LLM or embedding-based search for better LTX-Video prompt suggestions.
2. [ ] **Auto-Documentation:** Implement a script to automatically update `conductor/tech-stack.md` based on `requirements.txt` changes.

### Tier 2: Performance & Polish
1. [ ] **Performance Profiling:** Integrate `cProfile` into the engine to identify bottleneck functions.
2. [ ] **UI Animation:** Add subtle entry/exit animations to view transitions for a more fluid "Technoid" feel.

## Completed (Mar 2026 Refactor)
- [x] Create **API Load Testing** utility (`tools/api_load_test.py`).
- [x] Create **Model Checkpoint Tests** (integrity and existence checks).
- [x] Refactor and unify setup/start into **studio.bat** and **studio.sh**.
- [x] Consolidate video dependencies into a single **requirements.txt**.
- [x] Create **automated unit tests** for system utilities.
- [x] Create **CONTRIBUTING.md** with framework and design guidelines.
- [x] Apply **Technoid Brutalist UI Unification** to all views.
- [x] Implement **Video Preview Modal** with subtitle support.
- [x] Implement **Project Search** (Filter) for voices, assets, and projects.
- [x] Implement **Auto-Cleanup** background thread for stale files.
- [x] Implement **Resource Monitoring** (CPU/RAM/GPU) in System Manager.
- [x] Implement **Generation Audit Log** (audit.json) for transparency.
- [x] Implement **Audio Effects** (EQ & Reverb) for atmospheric polish.
- [x] Implement **Scene Search** keyword-based prompt suggestions for LTX-Video.
- [x] Implement **Parallel Streaming Synthesis** with look-ahead for ultra-low latency.
- [x] Implement **Persistent System Settings** (settings.json).
- [x] Implement **Phoneme Editor Bulk Import** (JSON).
- [x] Implement **AI Watermarking** (Audible & Visible).
- [x] Implement **LTX-Video Advanced Tuning** (Guidance, Steps, Seed).
- [x] Implement **Dual-Track Streaming TTS** for low-latency previews.
- [x] Implement **Phoneme Editor** UI and backend.
- [x] Implement **Subtitle Generation** (.srt) for narrated videos.
- [x] Implement **Instruction Brackets** support for emotional cues.
- [x] Document the `TaskManager` class.
- [x] Add type hints to `PodcastEngine` methods.
- [x] Standardize error handling in `voices.py`.
- [x] Refactor `src/static/app.js` into modular ES files.
- [x] Update `conductor/product.md`.
- [x] Create missing `README.md` for `src/backend/qwen_tts/core/`.
- [x] Implement Unified Model Inventory UI.
- [x] Integrate Video Generation (LTX) into workflow.
- [x] Enhance environment setup with CUDA detection.
- [x] Cleaned stale logs, projects, and dummy uploads.

## Awaiting Human Feedback
- (All current structural feedback addressed)
