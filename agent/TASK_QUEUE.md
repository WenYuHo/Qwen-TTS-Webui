# TASK QUEUE: QWEN-TTS
# LAST_GLOBAL_SYNC: 2026-03-09T01:05:31Z

## ACTIVE SIGNALS
- **SYSTEM**: `BOOT_SEQUENCE_COMPLETE`

## PRIORITIZED BACKLOG

- [x] **DUBBING_SEGMENT_ORIGINAL_PREVIEW**
    - Task: Implement playback for individual diarized segments in the Dubbing UI to verify diarization quality before synthesis.
    - Ref: `src/static/dubbing.js`
    - Promise: `DUBBING_SEGMENT_PREVIEW_READY`
    - Reserved: gemini-cli-1 @ 2026-03-09T01:03:16Z
    - Updated: 2026-03-09T01:04:41Z
    - Signals: NONE

- [x] **STUDIO_TIMELINE_BLOCK_REORDER**
    - Task: Implement drag-and-drop reordering for blocks in the Project Studio Production view.
    - Ref: `src/static/timeline.js`
    - Promise: `STUDIO_REORDER_READY`
    - Reserved: NONE
    - Updated: 2026-03-09T01:05:31Z
    - Signals: NONE

- [ ] **UI_GLOBAL_ACCENT_PICKER**
    - Task: Add a theme accent color picker to the System view to allow customizing the Studio's signature "Volt" color.
    - Ref: `src/static/style.css`
    - Promise: `UI_ACCENT_PICKER_LIVE`
    - Reserved: NONE
    - Updated: 2026-03-09T01:05:00Z
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
