# Specification: Tokenizer and Generation Stability Fixes

## Overview
This track addresses two critical stability issues in the Qwen-TTS model loading and generation process:
1.  **Tokenizer Regex Fix:** The Mistral-based tokenizer requires a specific regex fix to prevent incorrect tokenization.
2.  **Missing `pad_token_id`:** The model currently lacks a standard `pad_token_id` mapping, leading to warnings and potential generation instability.

## Problem Statement
- A warning informs the user that the tokenizer is being loaded with an incorrect regex pattern, which can lead to degraded vocal quality.
- `transformers` logs a warning about setting `pad_token_id` to `eos_token_id` because it's not explicitly defined in the model's generation config.

## Objectives
- **Fix Tokenizer Loading:** Ensure `fix_mistral_regex=True` is correctly passed and respected during tokenizer initialization.
- **Explicit Pad Mapping:** Explicitly set `pad_token_id` in the model configuration to silence warnings and ensure consistent behavior across different `transformers` versions.

## Proposed Changes
### Core AI Logic
- **`src/backend/qwen_tts/inference/qwen3_tts_model.py`:** Update `from_pretrained` to more robustly handle the `fix_mistral_regex` flag and explicitly set `model.config.pad_token_id`.
- **`src/backend/qwen_tts/core/models/modeling_qwen3_tts.py`:** (If necessary) Update the `generate` method to ensure `pad_token_id` is utilized correctly.

## Success Criteria
- No "incorrect regex pattern" warning during model loading.
- No "Setting `pad_token_id` to `eos_token_id`" warning during generation.
- Automated synthesis tests still pass with correct output structure.
