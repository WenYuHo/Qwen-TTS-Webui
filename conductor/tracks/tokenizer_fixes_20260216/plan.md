# Implementation Plan: Tokenizer and Generation Stability Fixes

This plan follows a TDD approach.

## Phase 1: Robust Tokenizer Loading
Ensure the tokenizer regex fix is applied correctly.

- [ ] Task: Verify Tokenizer Regex Warning
    - [ ] Create a test that captures stdout/stderr during model loading to detect the warning.
- [ ] Task: Implement Tokenizer Regex Fix
    - [ ] Update `src/backend/qwen_tts/inference/qwen3_tts_model.py` to ensure `fix_mistral_regex=True` is passed to the tokenizer loader.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Robust Tokenizer Loading' (Protocol in workflow.md)

## Phase 2: Pad Token ID Mapping
Resolve generation warnings by explicitly setting the pad token.

- [ ] Task: Verify Pad Token Warning
    - [ ] Create a test that triggers generation and captures the `pad_token_id` warning.
- [ ] Task: Map Pad Token ID
    - [ ] Update `src/backend/qwen_tts/inference/qwen3_tts_model.py` to explicitly set `model.config.pad_token_id = model.config.tts_pad_token_id`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Pad Token ID Mapping' (Protocol in workflow.md)

## Phase 3: Final Verification
Ensure all fixes work together without regressions.

- [ ] Task: Full System Health & Synthesis Test
    - [ ] Run `tests/test_e2e_synthesis.py` and verify zero stability warnings in logs.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Final Verification' (Protocol in workflow.md)
