# TASK QUEUE: QWEN-TTS
# LAST_GLOBAL_SYNC: 2026-03-09T03:09:28Z

## ACTIVE SIGNALS
- **SYSTEM**: `BOOT_SEQUENCE_COMPLETE`

## PRIORITIZED BACKLOG

- [x] **UI_EMOTIONAL_BRACKET_PARSING** (2026-03-10)
    - Task: Implement parsing for emotional tags in scripts (e.g., `[happy]`, `[whispering]`) and map them to Qwen3-TTS `instruct` parameters for expressive delivery.

- [x] **VIDEO_MULTIMODAL_SYNC_ENHANCEMENT** (2026-03-10)
    - Task: Improve the precision of audio-video alignment between Qwen3-TTS and LTX-Video, using waveform analysis to ensure frame-accurate synchronization.

- [x] **AUDIO_SPATIAL_SCENE_MAPPING** (2026-03-10)
    - Task: Add "Acoustic Environment" presets (Hall, Small Room, Stadium) that apply reverb and spatialization to synthesized voices.

- [ ] **VIDEO_CINEMATIC_CAMERA_CONTROLS**
    - Task: Expose LTX-Video camera movement parameters (dolly, tilt, pan, zoom) in the Video Production UI for cinematic control.
    - Ref: `track-narrated-video.md` (Task 1.3)
    - Promise: `CINEMATIC_CONTROLS_READY`
    - Reserved: NONE
    - Updated: 2026-03-10T11:15:00Z
    - Signals: NONE

- [ ] **TESTING_FIX_BROKEN_TESTS**
    - Task: Run the full test suite (`pytest tests/ -v`), identify failures/skips, and fix them (e.g., missing imports, hardware requirements, flaky async).
    - Ref: `track-testing-reliability.md` (Task 1.2)
    - Promise: `TESTS_FIXED_AND_GREEN`
    - Reserved: Antigravity @ 2026-03-09T21:17:00Z
    - Updated: 2026-03-09T21:17:00Z
    - Signals: NONE

- [ ] **TESTING_CONFT_UPGRADE_FIXTURES**
    - Task: Upgrade `tests/conftest.py` with reusable fixtures (`mock_model`, `mock_engine`, `app_client`, `test_audio`) to simplify unit and integration testing.
    - Ref: `track-testing-reliability.md` (Task 1.3)
    - Promise: `TEST_FIXTURES_UPGRADED`
    - Reserved: NONE
    - Updated: 2026-03-09T19:25:00Z
    - Signals: NONE

- [ ] **TESTING_PODCAST_ENGINE_UNIT_TESTS**
    - Task: Implement comprehensive unit tests in `tests/test_engine.py` covering all `generate_segment` modes (preset, design, clone) and error cases.
    - Ref: `track-testing-reliability.md` (Task 2.1)
    - Promise: `ENGINE_UNIT_TESTS_READY`
    - Reserved: NONE
    - Updated: 2026-03-09T19:25:00Z
    - Signals: NONE

- [x] **VIDEO_PROMPT_ARCHITECT_ENHANCEMENT**
    - Task: Enhance `suggest_video_scene` in `src/backend/api/video.py` with more atmospheres (documentary, action, comedy), character descriptions, and LTX-2 quality suffixes.
    - Ref: `track-narrated-video.md` (Task 3.2)
    - Promise: `VIDEO_PROMPT_ENHANCED`
    - Reserved: gemini-cli-1 @ 2026-03-09T19:10:00Z
    - Updated: 2026-03-09T19:10:00Z
    - Signals: NONE

- [x] **VIDEO_SCENE_PREVIEW_THUMBNAILS**
    - Task: Add `/api/video/preview-scene` endpoint to generate single-frame thumbnails using LTX-2 for fast visual verification before full rendering.
    - Ref: `track-narrated-video.md` (Task 3.1)
    - Promise: `VIDEO_PREVIEW_READY`
    - Reserved: gemini-cli-1 @ 2026-03-09T19:15:00Z
    - Updated: 2026-03-09T19:15:00Z
    - Signals: NONE

- [x] **VIDEO_BATCH_RENDERING_QUEUE**
    - Task: Implement `/api/video/narrated/batch` endpoint to submit multiple video jobs sequentially, integrated with the existing task manager.
    - Ref: `track-narrated-video.md` (Task 3.3)
    - Promise: `VIDEO_BATCH_QUEUE_LIVE`
    - Reserved: gemini-cli-1 @ 2026-03-09T19:20:00Z
    - Updated: 2026-03-09T19:20:00Z
    - Signals: NONE

- [x] **PRODUCTION_MULTI_SCENE_SCHEMA**
    - Task: Implement Multi-Scene schema support in `schemas.py` and extend `NarratedVideoRequest` for professional video production.
    - Ref: `track-narrated-video.md` (Task 1.1)
    - Promise: `VIDEO_SCENE_SCHEMA_READY`
    - Reserved: gemini-cli-1 @ 2026-03-09T03:06:01Z
    - Updated: 2026-03-09T03:09:16Z
    - Signals: NONE

- [x] **TESTING_COVERAGE_BASELINE**
    - Task: Generate a comprehensive coverage report and create `tests/coverage_baseline.md` to identify reliability gaps.
    - Ref: `track-testing-reliability.md` (Task 1.1)
    - Promise: `COVERAGE_BASELINE_READY`
    - Reserved: gemini-cli-1 @ 2026-03-09T03:09:28Z
    - Updated: 2026-03-09T03:25:00Z
    - Signals: NONE

- [x] **PRODUCTION_UI_SUBTITLE_CONTROLS**
    - Task: Add UI controls for subtitle enabling, position, and font size in the video production section.
    - Ref: `track-narrated-video.md` (Task 2.3)
    - Promise: `UI_SUBTITLE_CONTROLS_LIVE`
    - Reserved: gemini-cli-1 @ 2026-03-09T03:35:00Z
    - Updated: 2026-03-09T03:35:00Z
    - Signals: NONE

- [x] **MULTI_SCENE_NARRATED_VIDEO_ENGINE**
    - Task: Implement sequential scene generation and concatenation in `src/backend/api/video.py` using MoviePy to support professional multi-scene video production.
    - Ref: `track-narrated-video.md` (Task 1.2)
    - Promise: `MULTI_SCENE_ENGINE_READY`
    - Reserved: gemini-cli-1 @ 2026-03-09T18:45:00Z
    - Updated: 2026-03-09T18:45:00Z
    - Signals: NONE

- [x] **VIDEO_SUBTITLE_BURNING_SERVICE**
    - Task: Create `src/backend/utils/subtitles.py` to generate SRT and burn subtitles into the video using MoviePy TextClip for permanent accessibility.
    - Ref: `track-narrated-video.md` (Task 2.2)
    - Promise: `SUBTITLE_BURNING_SERVICE_READY`
    - Reserved: gemini-cli-1 @ 2026-03-09T18:50:00Z
    - Updated: 2026-03-09T18:50:00Z
    - Signals: NONE

- [x] **SYSTEM_LANGUAGES_ENUMERATION**
    - Task: Add `/api/system/languages` endpoint to return all 10 languages and 6 Chinese dialects supported by Qwen3-TTS, and update the UI to dynamically load them.
    - Ref: `track-multilingual-accessibility.md` (Task 1.1)
    - Promise: `SYSTEM_LANGUAGES_ENUMERATED`
    - Reserved: gemini-cli-1 @ 2026-03-09T18:55:00Z
    - Updated: 2026-03-09T18:55:00Z
    - Signals: NONE

- [x] **PRODUCTION_UI_MULTI_SCENE_EDITOR**
    - Task: Implement a visual scene editor in the video production tab to allow users to add, reorder, and configure multiple scenes (prompts, narration, voices).
    - Ref: `track-narrated-video.md` (Task 1.4)
    - Promise: `UI_MULTI_SCENE_EDITOR_READY`
    - Reserved: gemini-cli-1 @ 2026-03-09T19:05:00Z
    - Updated: 2026-03-09T19:05:00Z
    - Signals: NONE

- [x] **SYSTEM_UI_I18N_ENGINE**
    - Task: Implement `src/static/i18n.js` and extract UI strings to JSON files (EN/ZH) to support a multilingual interface.
    - Ref: `track-multilingual-accessibility.md` (Task 2.1)
    - Promise: `UI_I18N_ENGINE_LIVE`
    - Reserved: gemini-cli-1 @ 2026-03-09T19:15:00Z
    - Updated: 2026-03-09T19:15:00Z
    - Signals: NONE

- [x] **PRODUCTION_VIDEO_RESOLUTION_PRESETS**
    - Task: Add aspect ratio selection (9:16, 16:9, 1:1) to the video UI and map them to LTX-compatible dimensions (divisible by 32).
    - Ref: `track-narrated-video.md` (Task 3.4)
    - Promise: `VIDEO_RESOLUTION_PRESETS_READY`
    - Reserved: gemini-cli-1 @ 2026-03-09T19:25:00Z
    - Updated: 2026-03-09T19:25:00Z
    - Signals: NONE

- [x] **DUBBING_AUTO_LANGUAGE_DETECTION**
    - Task: Modify `PodcastEngine.transcribe_audio` to return detected language and segments, add `/api/generate/detect-language` endpoint, and wire the UI.
    - Ref: `track-dubbing-pipeline.md` (Task 1.1)
    - Promise: `DUBBING_LANG_DETECT_READY`
    - Reserved: gemini-cli-1 @ 2026-03-09T19:45:00Z
    - Updated: 2026-03-09T19:45:00Z
    - Signals: NONE

- [x] **DUBBING_PROGRESS_TRACKING**
    - Task: Implement `run_dubbing_task` background worker with step-by-step progress updates and wire the frontend to use `TaskManager.pollTask`.
    - Ref: `track-dubbing-pipeline.md` (Task 1.2)
    - Promise: `DUBBING_PROGRESS_LIVE`
    - Reserved: gemini-cli-1 @ 2026-03-09T19:45:00Z
    - Updated: 2026-03-09T19:45:00Z
    - Signals: NONE

- [x] **DUBBING_SOURCE_PREVIEW_WAVESURFER**
    - Task: Enhance the dubbing UI to show a WaveSurfer waveform and persistent player for source audio immediately after upload.
    - Ref: `track-dubbing-pipeline.md` (Task 1.3)
    - Promise: `DUBBING_SOURCE_PREVIEW_READY`
    - Reserved: gemini-cli-1 @ 2026-03-09T19:45:00Z
    - Updated: 2026-03-09T19:45:00Z
    - Signals: NONE

## COMPLETED
- [x] **ENGINE_REFACTOR_MODULAR** (2026-03-07)
- [x] **DUBBING_PH1** (2026-03-07)
- [x] **VIDEO_GEN_SETUP** (2026-03-07)
- [x] **DUBBING_S2S_PH2** (2026-03-07)
...
- [x] **UI_QUICK_SHARE_LINK** (2026-03-09)
- [x] **DUBBING_SYNC_REFINEMENT** (2026-03-09)
- [x] **PRODUCTION_AUTO_SUBTITLES** (2026-03-09)
- [x] **ENGINE_VRAM_OPTIMIZATION** (2026-03-09)
- [x] **PRODUCTION_EXPORT_FORMATS** (2026-03-09)
- [x] **UI_SAMPLE_SCRIPTS** (2026-03-09)
- [x] **UI_VOICE_STUDIO_RESET** (2026-03-09)
- [x] **UI_GUIDED_HELP_OVERLAY** (2026-03-09)
