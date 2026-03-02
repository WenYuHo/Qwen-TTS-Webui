# Qwen-TTS Core

This directory contains the foundational model architectures and tokenization logic for the Qwen-TTS 12Hz and 25Hz implementations.

## Directory Structure

- **`models/`**: Core modeling, configuration, and processing logic for the Qwen3-TTS architecture.
- **`tokenizer_12hz/`**: Specialized tokenizer implementation for the 12Hz frame-rate model (default). Includes the v2 modeling and configuration.
- **`tokenizer_25hz/`**: Legacy/Alternative tokenizer implementation for 25Hz models. Contains VQ (Vector Quantization) components including Whisper encoder and speech VQ logic.

## Usage

These components are typically not called directly. They are instantiated and managed by the `Qwen3TTSModel` and `Qwen3TTSTokenizer` classes in `src/backend/qwen_tts/inference/`.

## Key Dependencies

- **PyTorch**: For tensor operations and model execution.
- **Transformers**: Base library for model configuration and standard components.
- **Einops**: Used for flexible tensor rearrangements in core modeling logic.
