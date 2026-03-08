# TASK QUEUE: QWEN-TTS
# LAST_GLOBAL_SYNC: 2026-03-08T23:45:00Z

## ACTIVE SIGNALS
- **SYSTEM**: `BOOT_SEQUENCE_COMPLETE`

## PRIORITIZED BACKLOG

- [x] **ENGINE_REFACTOR_MODULAR**
    - Task: Decompose `src/backend/podcast_engine.py` -> Segmenter, Synthesizer, Patcher modules.
    - Ref: `conductor/tech-stack.md` (Code Quality).
    - Promise: `ENGINE_REFACTOR_MODULAR`
    - Reserved: NONE
    - Updated: 2026-03-07T18:15:00Z
    - Signals: `NONE`

- [x] **VOICE_CLONE_E2E_API**
    - Task: E2E API tests for voice cloning (upload, generate, status).
    - Ref: `conductor/track-testing-reliability.md` (3.2).
    - Promise: `VOICE_CLONE_E2E_API`
    - Reserved: NONE
    - Updated: 2026-03-07T23:15:00Z
    - Signals: `NONE`

- [x] **E2E_UI_FLOW_TESTED**
    - Task: Playwright E2E tests for synthesis and video gen flows.
    - Ref: `conductor/track-testing-reliability.md` (Ph3).
    - Promise: `E2E_UI_FLOW_TESTED`
    - Reserved: NONE
    - Updated: 2026-03-07T23:30:00Z
    - Signals: `NONE`

- [x] **TEST_LIBRARY_AUDIT** (2026-03-08)
- [x] **TEST_REFACTOR_PYTEST** (2026-03-08)
- [x] **TEST_CONSOLIDATE_ROOT** (2026-03-08)
- [x] **TEST_ASYNC_STANDARDIZATION**
    - Task: Standardize on `httpx.AsyncClient` for all API tests for better async flow coverage.
    - Ref: `agent/TESTING_AUDIT_REPORT.md`
    - Promise: `TEST_ASYNC_STANDARDIZATION`
    - Reserved: gemini-cli-1 @ 2026-03-08T22:49:11Z
    - Updated: 2026-03-08T22:54:14Z
    - Signals: `NONE`

- [x] **TEST_POLLUTION_FIX**
    - Task: Address test state pollution causing failures in `test_api.py` when run in batch.
    - Ref: Recent `pytest` run failures.
    - Promise: `TEST_POLLUTION_FIX`
    - Reserved: gemini-cli-1 @ 2026-03-08T22:55:00Z
    - Updated: 2026-03-08T23:10:00Z
    - Signals: `NONE`

- [x] **TORCH_COMPAT_FIX**
    - Task: Fix `TypeError` in `dynamic_range_compression_torch` for Python 3.13 compatibility.
    - Ref: `src/backend/qwen_tts/core/models/modeling_qwen3_tts.py`.
    - Promise: `TORCH_COMPAT_FIX`
    - Reserved: gemini-cli-1 @ 2026-03-08T23:10:00Z
    - Updated: 2026-03-08T23:15:00Z
    - Signals: `NONE`

- [x] **AUDIO_QUALITY_CI**
    - Task: Integrate `audio_quality_audit.py` into a post-deploy CI check.
    - Ref: `conductor/track-testing-reliability.md`.
    - Promise: `AUDIO_QUALITY_CI`
    - Reserved: gemini-cli-1 @ 2026-03-08T23:15:00Z
    - Updated: 2026-03-08T23:20:00Z
    - Signals: `NONE`

## COMPLETED
- [x] **ENGINE_REFACTOR_MODULAR** (2026-03-07)
- [x] **DUBBING_PH1** (2026-03-07)
- [x] **VIDEO_GEN_SETUP** (2026-03-07)
- [x] **DUBBING_S2S_PH2** (2026-03-07)
- [x] **TEST_ASYNC_STANDARDIZATION** (2026-03-08)
- [x] **TEST_POLLUTION_FIX** (2026-03-08)
- [x] **TORCH_COMPAT_FIX** (2026-03-08)
- [x] **AUDIO_QUALITY_CI** (2026-03-08)
