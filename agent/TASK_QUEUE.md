# TASK QUEUE: QWEN-TTS
# LAST_GLOBAL_SYNC: 2026-03-09T02:15:26Z

## ACTIVE SIGNALS
- **SYSTEM**: `BOOT_SEQUENCE_COMPLETE`

## PRIORITIZED BACKLOG

- [x] **DUBBING_VISUAL_FEEDBACK**
    - Task: Add a visual overlay/indicator in the Studio UI to show which segment is currently being synthesized during dubbing tasks.
    - Ref: `src/static/dubbing.js`
    - Promise: `DUBBING_VISUALS_LIVE`
    - Reserved: gemini-cli-1 @ 2026-03-09T01:42:00Z
    - Updated: 2026-03-09T01:46:24Z
    - Signals: NONE

- [x] **ENGINE_AUDIO_NORMALIZATION**
    - Task: Implement automatic LUFS normalization for the final podcast output to ensure consistent loudness across different voices and BGM.
    - Ref: `src/backend/engine_modules/patcher.py`
    - Promise: `LOUDNESS_NORMALIZED`
    - Reserved: gemini-cli-1 @ 2026-03-09T01:46:34Z
    - Updated: 2026-03-09T01:48:03Z
    - Signals: NONE

- [x] **PRODUCTION_EXPORT_FORMATS**
    - Task: Add support for exporting projects in AAC and FLAC formats in addition to WAV in the Production view.
    - Ref: `src/backend/api/projects.py`
    - Promise: `MULTI_FORMAT_EXPORT_READY`
    - Reserved: gemini-cli-1 @ 2026-03-09T01:48:13Z
    - Updated: 2026-03-09T02:15:26Z
    - Signals: NONE

## COMPLETED
- [x] **ENGINE_REFACTOR_MODULAR** (2026-03-07)
- [x] **DUBBING_PH1** (2026-03-07)
- [x] **VIDEO_GEN_SETUP** (2026-03-07)
- [x] **DUBBING_S2S_PH2** (2026-03-07)
- [x] **VOICE_CLONE_E2E_API** (2026-03-08)
- [x] **E2E_UI_FLOW_TESTED** (2026-03-08)
- [x] **TEST_LIBRARY_AUDIT** (2026-03-08)
- [x] **TEST_REFACTOR_PYTEST** (2026-03-08)
- [x] **TEST_CONSOLIDATE_ROOT** (2026-03-08)
- [x] **TEST_ASYNC_STANDARDIZATION** (2026-03-08)
- [x] **TEST_POLLUTION_FIX** (2026-03-08)
- [x] **TORCH_COMPAT_FIX** (2026-03-08)
- [x] **AUDIO_QUALITY_CI** (2026-03-08)
- [x] **DUBBING_S2S_STREAMING** (2026-03-08)
- [x] **MODEL_WEIGHTS_PRUNING** (2026-03-08)
- [x] **API_HEALTH_DASHBOARD** (2026-03-08)
- [x] **MODEL_INT8_QUANTIZATION** (2026-03-09)
- [x] **UI_MOBILE_OPTIMIZATION** (2026-03-09)
- [x] **DUBBING_LIP_SYNC_FEAT** (2026-03-09)
- [x] **DUBBING_PH3_MULTI_SPEAKER** (2026-03-09)
- [x] **ENGINE_DISK_CACHE** (2026-03-09)
- [x] **UI_SYSTEM_METRICS_FOOTER** (2026-03-09)
- [x] **DUBBING_SEGMENT_ORIGINAL_PREVIEW** (2026-03-09)
- [x] **STUDIO_TIMELINE_BLOCK_REORDER** (2026-03-09)
- [x] **UI_GLOBAL_ACCENT_PICKER** (2026-03-09)
- [x] **DUBBING_BATCH_RETRY_LOGIC** (2026-03-09)
- [x] **UI_ASSET_METADATA_VIEWER** (2026-03-09)
- [x] **ENGINE_PROMPT_EMBEDDING_CACHE** (2026-03-09)
- [x] **UI_TASK_HISTORY_VIEW** (2026-03-09)
- [x] **ENGINE_AUTO_BACKUP** (2026-03-09)
- [x] **UI_QUICK_SHARE_LINK** (2026-03-09)
- [x] **DUBBING_SYNC_REFINEMENT** (2026-03-09)
- [x] **PRODUCTION_AUTO_SUBTITLES** (2026-03-09)
- [x] **ENGINE_VRAM_OPTIMIZATION** (2026-03-09)
