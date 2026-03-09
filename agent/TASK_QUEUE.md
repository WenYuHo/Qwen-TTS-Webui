# TASK QUEUE: QWEN-TTS
# LAST_GLOBAL_SYNC: 2026-03-09T01:35:36Z

## ACTIVE SIGNALS
- **SYSTEM**: `BOOT_SEQUENCE_COMPLETE`

## PRIORITIZED BACKLOG

- [x] **DUBBING_SYNC_REFINEMENT**
    - Task: Implement precise segment-level timing refinement for dubbed audio to match original video cadence using cross-correlation or silence padding.
    - Ref: `conductor/track-dubbing-pipeline.md`
    - Promise: `DUBBING_SYNC_REFINED`
    - Reserved: gemini-cli-1 @ 2026-03-09T01:32:31Z
    - Updated: 2026-03-09T01:33:37Z
    - Signals: NONE

- [x] **PRODUCTION_AUTO_SUBTITLES**
    - Task: Automatically generate SRT/VTT sidecar files for every Produced Project and add an option to burn-in subtitles during MP4 export.
    - Ref: `conductor/track-multilingual-accessibility.md`
    - Promise: `AUTO_SUBTITLES_READY`
    - Reserved: NONE
    - Updated: 2026-03-09T01:35:36Z
    - Signals: NONE

- [ ] **ENGINE_VRAM_OPTIMIZATION**
    - Task: Implement a unified memory management strategy to handle the VRAM switch between Qwen-TTS and LTX-Video, minimizing "Out of Memory" errors during full production runs.
    - Ref: `conductor/track-sound-generation.md`
    - Promise: `VRAM_OPTIMIZED`
    - Reserved: gemini-cli-1 @ 2026-03-09T01:35:36Z
    - Updated: 2026-03-09T02:35:00Z
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
