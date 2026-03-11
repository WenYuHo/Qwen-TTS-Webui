# Testing Coverage Baseline — 2026-03-08

## OVERALL SUMMARY (STATIC AUDIT)

| Module | Lines | Status | Tests | Estimated Coverage |
|--------|-------|--------|-------|--------------------|
| **CORE BACKEND** | | | | |
| `src/backend/podcast_engine.py` | 537 | ✅ | `test_engine.py`, `test_e2e_synthesis.py` | >85% |
| `src/backend/task_manager.py` | 182 | ✅ | `test_task_manager.py`, `test_tasks_manager.py` | >90% |
| `src/backend/video_engine.py` | 297 | ✅ | `test_video_dubbing.py` | >80% |
| `src/backend/config.py` | 124 | ✅ | `test_config.py` | >90% |
| `src/backend/diarization.py` | 156 | ✅ | `test_multi_speaker.py` | >80% |
| `src/backend/dub_logic.py` | 213 | ✅ | `test_batch_resilience.py` | >70% |
| `src/backend/model_loader.py` | 189 | ✅ | `test_quantization_config.py` | >80% |
| **API LAYER** | | | | |
| `src/backend/api/generation.py` | 163 | ✅ | `test_voicelab_integration.py`, `test_api.py` | >80% |
| `src/backend/api/assets.py` | 112 | ✅ | `test_assets_api.py` | >90% |
| `src/backend/api/projects.py` | 145 | ✅ | `test_projects_api.py` | >80% |
| `src/backend/api/system.py` | 89 | ✅ | `test_system_api.py` | >90% |
| `src/backend/api/voices.py` | 124 | ✅ | `test_voice_preview.py` | >80% |
| `src/backend/api/schemas.py` | 240 | ✅ | `test_narrated_video_schema.py` | >90% |
| **UTILITIES** | | | | |
| `src/backend/utils/__init__.py` | 433 | ✅ | `test_system_utils.py`, `test_phoneme_manager.py` | >80% |
| `src/backend/utils/cache.py` | 156 | ✅ | `test_engine_cache.py` | >90% |
| `src/backend/utils/lip_sync.py` | 112 | ✅ | `test_lip_sync.py` | >80% |
| `src/backend/utils/subtitles.py` | 89 | ❌ | **NONE** | 0% |
| **QWEN_TTS CORE** | | | | |
| `src/backend/qwen_tts/finetuning/` | - | ❌ | **NONE** | 0% |
| `src/backend/qwen_tts/cli/demo.py` | - | ❌ | **NONE** | 0% |
| `src/backend/engine_modules/segmenter.py` | - | ⚠️ | Integration only | <30% |

## RELIABILITY GAPS

### 1. Missing Module Unit Tests
- **`src/backend/utils/subtitles.py`**: Handles SRT generation and captioning. Needs dedicated unit tests for various subtitle formats.
- **`src/backend/qwen_tts/finetuning/`**: Core finetuning logic (dataset, sft) is untested. Critical for custom model training stability.
- **`src/backend/qwen_tts/cli/demo.py`**: Manual testing only.

### 2. Integration Dependencies
- Many tests rely on `sox_shim.mock_sox()` in `conftest.py`. While good for unit tests, E2E tests need a real environment to verify audio quality.

### 3. Asynchronous Race Conditions
- `test_tasks_manager.py` shows potential flakiness in high-load scenarios.

## TARGET: >80% on all core modules.
**Priority gaps:** Modules below 50% (`subtitles.py`, `finetuning/`).

---
*Note: This report was generated via static analysis of the test suite and source mapping due to environment restrictions on running live coverage tools.*
