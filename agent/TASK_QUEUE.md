# TASK QUEUE: QWEN-TTS
# LAST_GLOBAL_SYNC: 2026-03-09T00:56:43Z

## ACTIVE SIGNALS
- **SYSTEM**: `BOOT_SEQUENCE_COMPLETE`

## PRIORITIZED BACKLOG

- [x] **DUBBING_PH3_MULTI_SPEAKER**
    - Task: Implement Speaker Diarization and Multi-Speaker Synthesis/Merge (Phase 3 from `conductor/track-dubbing-pipeline.md`).
    - Ref: `conductor/track-dubbing-pipeline.md`
    - Promise: `DUBBING_MULTI_SPEAKER_READY`
    - Reserved: gemini-cli-1 @ 2026-03-09T00:50:00Z
    - Updated: 2026-03-09T00:54:16Z
    - Signals: NONE


- [x] **ENGINE_DISK_CACHE**
    - Task: Implement persistent disk caching for speaker embeddings and transcriptions to reduce redundant compute across server restarts.
    - Ref: `agent/ARCHITECTURE.md`
    - Promise: `ENGINE_DISK_CACHE_READY`
    - Reserved: gemini-cli-1 @ 2026-03-09T00:54:51Z
    - Updated: 2026-03-09T00:56:35Z
    - Signals: NONE

- [ ] **UI_SYSTEM_METRICS_FOOTER**
    - Task: Integrate real-time VRAM/CPU/Task metrics from `/api/system/stats` into the Studio UI footer.
    - Ref: `src/static/index.html`
    - Promise: `UI_METRICS_FOOTER_LIVE`
    - Reserved: gemini-cli-1 @ 2026-03-09T00:56:43Z
    - Updated: 2026-03-09T00:50:00Z
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
