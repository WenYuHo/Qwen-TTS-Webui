# Tech Stack: Qwen-TTS Podcast Studio (v2.1) 🎙️

## Backend
- **Core:** Python 3.9+ with FastAPI (ASGI Framework).
- **Server:** Uvicorn for local development and high-performance asynchronous serving.
- **Audio Processing:** Pydub (MP3/WAV/etc. manipulation), Soundfile (Numpy-based I/O), Librosa (Audio analysis).
- **AI/ML Integration:**
  - **Frameworks:** PyTorch, Transformers (Hugging Face).
  - **Runtime:** ONNX Runtime for optimized inference.
  - **Models:** Qwen-TTS for state-of-the-art text-to-speech synthesis.
- **Configuration:** python-dotenv for `.env`-based environment variable management.
- **Logging:** Centralized Python logging with `RotatingFileHandler` for automated log management.
- **Task Management:** Custom asynchronous `TaskManager` using FastAPI BackgroundTasks for non-blocking inference.
- **Performance Monitoring:** `psutil`-based system resource tracking (CPU/MEM utilization).

## Frontend
- **Frameworks:** Vanilla JavaScript (ES6+), CSS3 (Technoid Brutalist), HTML5.
- **Architecture:** Modular ES Modules (`task_manager.js`, `assets.js`, etc.).
- **Design Philosophy:** **Technoid Brutalist** (Onyx/Volt palette, sharp borders, multi-layered shadows).
- **Interactions:** Asynchronous API communication with the backend.

## Python Dependencies
<!-- DEPENDENCIES_START -->
- **API:** fastapi, uvicorn, python-multipart
- **Audio:** soundfile, numpy, pydub, librosa, scipy, torchaudio
- **AI/ML:** torch, transformers, accelerate, einops, onnxruntime, openai-whisper
- **Video:** ltx-pipelines, diffusers, opencv-python, moviepy, Pillow
- **Utils:** python-dotenv, psutil, huggingface_hub, deep-translator, beautifulsoup4, tqdm
- **Testing:** pytest, pytest-asyncio, httpx
<!-- DEPENDENCIES_END -->

## Infrastructure & Testing
- **Package Management:** `pip` with a virtual environment (`.venv`).
- **Testing:** `pytest` and `pytest-asyncio` for unit and integration tests.
- **Mocking:** `httpx` for asynchronous HTTP testing.
- **Model Storage:** References to model directories via `.env` configuration.
