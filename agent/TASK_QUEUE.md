# Task Queue: Autonomous Improvement

## Prioritized Backlog

### Tier 1: Documentation & Refinement
1. [~] Document the `TaskManager` class in `src/backend/task_manager.py`.
2. [ ] Add type hints to `src/backend/podcast_engine.py` methods.
3. [ ] Update `conductor/product.md` to reflect the reconciled "Technoid Brutalist" vs "Classic Studio" design direction.
4. [ ] Create missing `README.md` for `src/backend/qwen_tts/core/`.

### Tier 2: Code Quality
1. [ ] Refactor `src/static/app.js` to extract large UI-rendering functions into smaller, modular files.
2. [ ] Standardize error handling in `src/backend/api/voices.py` to use the centralized logger consistently.

### Tier 3: Innovation & Features (Brainstormed Mar 2026)
1. **Instruction Brackets:** Implement support for inline emotional cues like `[whispered]` or `[sarcastic]` in the script editor.
2. **Subtitle Generation:** Add a feature to automatically generate and export `.srt` or `.vtt` files for narrated videos.
3. **Phoneme Editor:** Create a UI component to fix mispronunciations using phonetic inputs.
4. **Streaming TTS:** Refactor the synthesis engine to support Dual-Track streaming for ~100ms latency previews.
5. **LTX-Video Advanced Tuning:** Add sliders for Guidance Scale, Inference Steps, and Seed selection in the Video Generation panel.
6. **Watermarking:** Integrate AI watermarking (audible or metadata) for compliance with transparency standards.

## Completed (Mar 2026 Refactor)
- [x] Consolidate all root-level `update_*.py` scripts into `tools/`.
- [x] Consolidate root-level `verify_*.py` scripts into `tools/`.
- [x] Delete redundant `AGENTS.md` and move rules to `conductor/`.
- [x] Implement Unified Model Inventory UI (Qwen + LTX).
- [x] Integrate Video Generation (LTX) into Project Studio workflow.
- [x] Enhance `setup_env.bat` with CUDA detection.
- [x] Cleaned stale logs, projects, and dummy uploads.

## Awaiting Human Feedback
- Should we move `setup_env.sh` and `start.sh` into a `bin/` or `scripts/` folder? (Standard practice vs ease of use).
