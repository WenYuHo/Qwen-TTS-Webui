# Recent Milestones & Context

*   **Bolt Optimizations**: We recently implemented "Bolt" optimizations in `podcast_engine.py` (e.g., caching audio watermark tones, lazy loading models, using `soundfile` instead of `librosa` for speed).
*   **ICL Cloning Overhaul**: Voice cloning uses `ref_text` for In-Context Learning (ICL) in Qwen-TTS. It works via concatenating the reference audio with the target text.
*   **LTX-Video Integrated**: Video generation is live via endpoints in `video.py`.
*   **ACX Mastering Added**: `utils.AudioPostProcessor` now contains ACX audio compliance normalization.
*   **Dubbing Phase 1 Started**: `PodcastEngine.transcribe_audio()` now returns full Whisper metadata (text, language, segments). Added `/api/generate/detect-language` endpoint and a "DETECT" button in the Dubbing UI to auto-fill target languages.
*   **Voice Clone E2E Hardened**: Fixed `temperature` keyword argument bug in `api/generation.py` and added `tests/test_voice_clone_e2e.py` covering the full API workflow.
*   **Testing Coverage Baseline Established**: Static audit performed across all core modules; `tests/coverage_baseline.md` created to identify reliability gaps.
*   **Subtitle UI Controls Live**: Added position and font size controls to the video production section; integrated with `VideoModal` overlay for dynamic previewing.
