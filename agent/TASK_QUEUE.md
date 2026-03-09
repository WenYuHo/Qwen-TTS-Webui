# TASK QUEUE: QWEN-TTS
# LAST_GLOBAL_SYNC: 2026-03-09T01:08:26Z

## ACTIVE SIGNALS
- **SYSTEM**: `BOOT_SEQUENCE_COMPLETE`

## PRIORITIZED BACKLOG

- [ ] **DUBBING_BATCH_RETRY_LOGIC**
    - Task: Implement segment-level retry logic and partial success reporting for batch S2S dubbing.
    - Ref: `src/backend/dub_logic.py`
    - Promise: `DUBBING_BATCH_ROBUST`
    - Reserved: gemini-cli-1 @ 2026-03-09T01:08:26Z
    - Updated: 2026-03-09T01:10:00Z
    - Signals: NONE

- [ ] **UI_ASSET_METADATA_VIEWER**
    - Task: Add metadata display (duration, sample rate) and mini-waveform previews to the Asset Library.
    - Ref: `src/static/assets.js`
    - Promise: `ASSET_METADATA_READY`
    - Reserved: NONE
    - Updated: 2026-03-09T01:10:00Z
    - Signals: NONE

- [ ] **ENGINE_PROMPT_EMBEDDING_CACHE**
    - Task: Pre-calculate and disk-cache embeddings for common style prompts to eliminate "Voice Design" latency.
    - Ref: `src/backend/podcast_engine.py`
    - Promise: `PROMPT_CACHE_READY`
    - Reserved: NONE
    - Updated: 2026-03-09T01:10:00Z
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
