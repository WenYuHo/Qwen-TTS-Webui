# Qwen-TTS Studio: API Reference

This document provides a comprehensive reference for all REST API endpoints available in the Qwen-TTS Podcast Studio. All endpoints are prefixed with `/api`.

## 1. Voices & Library (`/api/voices`)

### `GET /library`
- **Description:** Retrieve all saved voice profiles.
- **Response:** `{"voices": [...]}`

### `POST /library`
- **Description:** Save or update the entire voice library.
- **Request:** `VoiceLibrary` schema (List of SpeakerProfiles).

### `POST /design`
- **Description:** Create a new voice from a text description.
- **Request:** `{"text": "...", "instruct": "..."}`
- **Response:** `{"task_id": "...", "status": "pending"}`

### `POST /mix`
- **Description:** Validate a mixed voice configuration.
- **Request:** `MixRequest` schema.

---

## 2. Generation (`/api/generate`)

### `POST /segment`
- **Description:** Synthesize a single script block.
- **Request:** `SynthesisRequest` schema.
- **Response:** `{"task_id": "...", "status": "pending"}`

### `POST /podcast`
- **Description:** Generate a full multi-character podcast with BGM.
- **Request:** `PodcastRequest` schema (includes `stream: bool` option).
- **Response:** `StreamingResponse` (audio/wav) OR `{"task_id": "...", "status": "pending"}`

### `POST /stream`
- **Description:** Low-latency streaming preview for a single block.
- **Request:** `StreamingSynthesisRequest`.
- **Response:** `StreamingResponse` (audio/wav).

### `POST /dub`
- **Description:** Automatically translate and dub an audio/video file.
- **Request:** `DubRequest`.

---

## 3. Video (`/api/video`)

### `POST /generate`
- **Description:** Generate an LTX-Video from a prompt.
- **Request:** `VideoGenerationRequest`.

### `POST /narrated`
- **Description:** Generate a narrated video (TTS + LTX-Video + Subtitles).
- **Request:** `NarratedVideoRequest`.

### `POST /suggest`
- **Description:** Analyze script text and suggest cinematic LTX prompts.
- **Request:** `{"text": "..."}`

---

## 4. Tasks (`/api/tasks`)

### `GET /`
- **Description:** List all active and recent background tasks.

### `GET /{task_id}`
- **Description:** Get detailed status, progress, and result metadata for a task.

### `DELETE /{task_id}`
- **Description:** Cancel a running task or clear it from the registry.

### `GET /{task_id}/result`
- **Description:** Download the final artifact (WAV/MP4) produced by a task.

---

## 5. System (`/api/system`)

### `GET /stats`
- **Description:** Real-time resource usage (CPU, RAM, GPU, Storage).

### `POST /benchmark`
- **Description:** Run a profiled synthesis and return `cProfile` breakdown.

### `GET /settings`
- **Description:** Retrieve system-wide preferences (Watermarking, etc.).

### `POST /settings`
- **Description:** Update and persist system settings.

### `GET /phonemes`
- **Description:** Retrieve the custom pronunciation dictionary.

---

## 6. Assets (`/api/assets`)

### `GET /`
- **Description:** List all uploaded media files in `shared_assets`.

### `POST /upload`
- **Description:** Upload a new media file (Multipart form).

### `DELETE /{filename}`
- **Description:** Delete a specific asset.
