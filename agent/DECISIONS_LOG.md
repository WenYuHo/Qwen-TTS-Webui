# Architectural Decisions Log (ADR)

This file tracks *why* critical architectural choices were made. AI agents should reference this to avoid re-litigating settled debates or misunderstanding the project's constraints.

## 1. No Modern Frontend Frameworks (React/Vue/Svelte)
*   **Date:** Project Inception
*   **Decision:** The frontend is strictly Vanilla JS and native Web Components / ES6 Modules.
*   **Reasoning:** To ensure raw performance, absolute control over the DOM for the complex audio timeline, and to reduce dependency bloat. The project relies on the "Technoid Brutalist" raw aesthetic, which aligns with raw web technologies.
*   **Implication:** Do not run `npx create-react-app` or introduce build steps (Webpack/Vite) unless specifically authorized in the tech stack.

## 2. Asynchronous Task Manager (`task_manager.py`)
*   **Date:** Pre-v2.0
*   **Decision:** A custom background task queue was built instead of using Celery or Redis.
*   **Reasoning:** Qwen-TTS inference takes significant time (seconds to minutes) and locks the GIL. Using Celery would introduce a massive external dependency (Redis/RabbitMQ). The custom `task_manager.py` using FastAPI `BackgroundTasks` keeps the project self-contained and easy for users to install locally.
*   **Implication:** Long-running API endpoints must return a `task_id` immediately and let the frontend poll `tasks.py` for progress.

## 3. Local Binaries over Global (`/bin` folder)
*   **Date:** March 2026
*   **Decision:** The project explicitly downloads and references `ffmpeg.exe` and `sox.exe` locally in the `/bin` directory.
*   **Reasoning:** Users frequently failed to properly install FFmpeg or SoX on their system PATH (especially on Windows). By packing them locally and updating `os.environ["PATH"]` in `config.py`, we guarantee the backend audio processing works flawlessly out of the box.
*   **Implication:** Do not assume `ffmpeg` is available system-wide; always rely on the path resolution in `config.py`.

## 4. "Bolt" Performance Optimizations
*   **Date:** March 2026
*   **Decision:** Shifted primary audio reading/writing from `librosa` and `pydub` back to `soundfile` wherever possible; cache watermark tones globally.
*   **Reasoning:** `librosa.load` is notoriously slow for large files. `soundfile` is C-backed and orders of magnitude faster. Time-to-first-audio is a critical UX metric for a podcast tool.
*   **Implication:** When doing simple I/O or sample-rate conversions, prefer `soundfile` or `sox_shim`. Only use `librosa` for spectral analysis or pitch shifting.

## 5. In-Context Learning (ICL) over Checkpoint fine-tuning for Clones
*   **Date:** March 2026
*   **Decision:** Voice cloning relies on zero-shot In-Context Learning (providing a 3-10s referent audio clip and its transcript to Qwen-TTS at generation time) rather than LoRA or full-finetuning.
*   **Reasoning:** High-quality finetuning requires hours of VRAM and clean data. ICL allows instant character creation, fitting the snappy UX goal.
*   **Implication:** `schemas.py` holds `ref_text` and `preview_text` to support this pattern. Do not attempt to build a PyTorch training loop for voice clones.
