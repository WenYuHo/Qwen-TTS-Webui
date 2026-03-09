# TASK QUEUE: QWEN-TTS
# LAST_GLOBAL_SYNC: 2026-03-09T00:25:50Z

## ACTIVE SIGNALS
- **SYSTEM**: `BOOT_SEQUENCE_COMPLETE`

## PRIORITIZED BACKLOG

- [ ] **MODEL_INT8_QUANTIZATION**
    - Task: Implement dynamic INT8 quantization for the Qwen-TTS model to reduce memory footprint and improve CPU inference speed.
    - Ref: `agent/ARCHITECTURE.md`
    - Promise: `MODEL_QUANTIZED_INT8`
    - Reserved: gemini-cli-1 @ 2026-03-09T00:25:50Z
    - Updated: 2026-03-09T00:30:00Z
    - Signals: NONE

- [ ] **UI_MOBILE_OPTIMIZATION**
    - Task: Refactor the Studio CSS to be fully responsive for mobile viewports, focusing on the timeline and voice laboratory controls.
    - Ref: `src/static/style.css`
    - Promise: `UI_MOBILE_READY`
    - Reserved: NONE
    - Updated: 2026-03-09T00:30:00Z
    - Signals: NONE

- [ ] **DUBBING_LIP_SYNC_FEAT**
    - Task: Add phoneme-level timestamp generation to the dubbing pipeline to support future lip-sync video generation.
    - Ref: `conductor/track-dubbing-pipeline.md`
    - Promise: `LIP_SYNC_METADATA_READY`
    - Reserved: NONE
    - Updated: 2026-03-09T00:30:00Z
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
