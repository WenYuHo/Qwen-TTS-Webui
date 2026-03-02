# Task Queue: Autonomous Improvement

## Prioritized Backlog

### Tier 1: Documentation & Governance
1. [ ] **API Documentation:** Create a static `API.md` file documenting all FastAPI endpoints, request schemas, and response formats.
2. [ ] **Unit Test Expansion:** Create automated tests for the new `Profiler` and `ResourceMonitor` classes.

### Tier 2: Performance & Intelligence
1. [ ] **Scene Search AI Upgrade:** Enhance the prompt suggestion logic with better cinematic components and action extraction.
2. [ ] **Performance Polish:** Add a "Clear Cache" button to the System view to purge the `PodcastEngine` in-memory caches.

## Completed (Mar 2026 Refactor)
- [x] Implement **Auto-Cleanup Stats** (Last Cleanup, Files Pruned) in System view.
- [x] Implement **Sub-Tab Autosave** for the System view using `localStorage`.
- [x] Refine **Error UI** with a "Copy Trace" button for troubleshooting.
- [x] Expand **automated unit tests** to cover Profiler, ResourceMonitor, and StorageManager.
- [x] Apply **Technoid Brutalist UI Unification** across all Studio views.
- [x] Implement **Help System** with context-sensitive command reference.
- [x] Implement **Toast Notifications** (non-blocking) replacing all `alert()` calls.
- [x] Implement **UI Animation** for smooth, fluid view transitions.
- [x] Implement **Performance Profiling Integration** (Benchmark sub-tab).
- [x] Implement **True Streaming** for podcast production.
- [x] Create **Model Integrity Tests** for checkpoints.
- [x] Consolidate setup/start into **studio.bat** and **studio.sh**.
- [x] Consolidate video dependencies into a single **requirements.txt**.
- [x] Create **CONTRIBUTING.md** with framework and design guidelines.
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
