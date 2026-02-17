# Implementation Plan: Tokenizer and Generation Stability Fixes

This plan follows a TDD approach.

## Phase 1: Robust Tokenizer Loading
Ensure the tokenizer regex fix is applied correctly.

- [x] Task: Verify Tokenizer Regex Warning
    - [x] Create a test that captures stdout/stderr during model loading to detect the warning.
- [x] Task: Implement Tokenizer Regex Fix
    - [x] Update `src/backend/qwen_tts/inference/qwen3_tts_model.py` to ensure `fix_mistral_regex=True` is passed to the tokenizer loader.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Robust Tokenizer Loading' (Protocol in workflow.md)

## Phase 2: Pad Token ID Mapping
Resolve generation warnings by explicitly setting the pad token.

- [x] Task: Verify Pad Token Warning
    - [x] Create a test that triggers generation and captures the `pad_token_id` warning.
- [x] Task: Map Pad Token ID
    - [x] Update `src/backend/qwen_tts/inference/qwen3_tts_model.py` to explicitly set `model.config.pad_token_id = model.config.tts_pad_token_id`.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Pad Token ID Mapping' (Protocol in workflow.md)

## Phase 3: Final Verification
Ensure all fixes work together without regressions.

- [x] Task: Full System Health & Synthesis Test
    - [x] Run `tests/test_e2e_synthesis.py` and verify zero stability warnings in logs.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Final Verification' (Protocol in workflow.md)

## Phase: Review Fixes
- [x] Task: Apply review suggestions
