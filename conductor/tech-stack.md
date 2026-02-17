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

## Frontend
- **Frameworks:** Vanilla JavaScript (ES6+), CSS3 (Glassmorphism), HTML5.
- **Design Philosophy:** Classic Studio aesthetic with modern tactile elements.
- **Interactions:** Asynchronous API communication with the backend.

## Infrastructure & Testing
- **Package Management:** `pip` with a virtual environment (`.venv`).
- **Testing:** `pytest` and `pytest-asyncio` for unit and integration tests.
- **Mocking:** `httpx` for asynchronous HTTP testing.
- **Model Storage:** References to model directories via `.env` configuration.
