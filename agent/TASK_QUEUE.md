# Task Queue: Autonomous Improvement

## Prioritized Backlog
- [x] **Sound Gen: Benchmark Baseline** — Create `tools/benchmark_tts.py` measuring latency/VRAM for all voice types. See `conductor/track-sound-generation.md` Phase 3 Task 3.1.
- [x] **Sound Gen: Silence Padding for ICL** — Append 0.5s silence to ref audio before ICL encoding to prevent phoneme bleed. See Track Phase 3 Task 3.3.
- [x] **Sound Gen: Reference Audio Validation** — Validate ref audio duration (3-30s) and reject silence-only input. See Track Phase 3 Task 3.4.
- [x] **Sound Gen: Temperature Presets** — Expose Consistent/Balanced/Creative temperature presets in UI. See Track Phase 3 Task 3.5.
- [ ] **Sound Gen: Per-Segment Quality Scoring** — Compute SNR/clipping metrics per segment. See Track Phase 4 Task 4.1.
- [ ] **Sound Gen: Auto-Retry on Low Quality** — Retry garbled segments with lower temperature. See Track Phase 4 Task 4.2.
- [ ] **Sound Gen: Unit Tests for Preview & ICL** — Tests for preview text pool, ICL mode toggle. See Track Phase 5.
- [ ] **Video Gen Auto-Setup:** Verify and automate the installation of `ltx-pipelines` and related dependencies if a GPU is detected.

## Completed (Mar 2026 Refactor)
- [x] **Environment Finalization:** Automated `ffmpeg` and `sox` setup via `tools/download_binaries.py` and integrated local `bin/` path into the backend.
- [x] **ACX Compliance Mastering:** Add an `AudioPostProcessor.normalize_acx` method and a "Master for Audible" toggle in the UI to ensure output meets RMS (-23dB to -18dB) and Peak (-3dB) standards.
- [x] **Enhanced Non-Verbal Tagging:** Update the script parser and backend to support mid-sentence non-verbal tags like `(laughs)`, `(sighs)`, or `[cheerful]` by segmenting the synthesis or appending instructions.
- [x] **LTX-2 Advanced Parameter Tuning:** Expose `max_shift`, `base_shift`, and `terminal` parameters in the Video generation UI/API for better motion control.
- [x] **Spatial Audio (Stereo Panning):** Add a `pan` attribute to voice profiles and script segments to allow spatial positioning of speakers in the stereo field.
- [x] **Storage Pruning Refinement:** Updated `StorageManager` to prevent deletion of `.gitkeep` files, ensuring empty directory structure preservation.
- [x] **Frontend Modularization:** Refactor `src/static/app.js` into modular ES files (`assets.js`, `system.js`, `production.js`, `task_manager.js`).
- [x] **Audit Log Implementation:** Track all synthesis and generation events in `audit.json` for governance.
- [x] **Project Persistence:** Added robust save/load for projects including settings and script draft.
- [x] **Modern UI:** Integrated Industrial/Cyberpunk aesthetics (Volt-text, glowing borders) across the UI.
- [x] **Integrate Video Generation (LTX) into workflow.**
- [x] **Enhance environment setup with CUDA detection.**
- [x] **Cleaned stale logs, projects, and dummy uploads.**

## Awaiting Human Feedback
- (All current structural feedback addressed)
