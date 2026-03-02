# Task Queue: Autonomous Improvement

## Prioritized Backlog

### Tier 1: Performance & Search
1. [ ] **API Load Testing:** Create a script to simulate concurrent generation requests and measure response times.
2. [ ] **Scene Search AI:** Upgrade keyword-based search to use a small LLM or embedding-based search for better suggestions.

### Tier 2: Governance & Automation
1. [ ] **Auto-Documentation:** Implement a script to automatically update `conductor/tech-stack.md` based on `requirements.txt` changes.
2. [ ] **Performance Profiling:** Integrate `cProfile` into the engine to identify bottleneck functions.

## Completed (Mar 2026 Refactor)
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
