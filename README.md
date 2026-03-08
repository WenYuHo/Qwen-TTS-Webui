# Qwen-TTS Podcast Studio (v3.0) 🎙️⚡

A professional, standalone web suite for high-fidelity audio and video production. Create stories, podcasts, and narrated cinematic scenes using **Qwen-TTS** and **LTX-Video**.

## 🤖 For AI Agents

This repository follows the **Conductor Framework**. Before starting any work, AI agents MUST read the following:
- **Project Index:** [conductor/index.md](conductor/index.md)
- **Workflow & Rules:** [conductor/workflow.md](conductor/workflow.md)
- **Agent Style Guide:** [conductor/code_styleguides/agent-improvement.md](conductor/code_styleguides/agent-improvement.md)
- **API Reference:** [API.md](API.md)

## ✨ Features

- **Multi-Model Studio**: Integrated support for Qwen-TTS (Audio) and LTX-Video (Narrated Video).
- **Technoid Brutalist UI**: A high-performance, industrial aesthetic with Volt accents and non-blocking interactions.
- **Voice Lab**: 
  - **Voice Design**: Create unique voices from text descriptions.
  - **Pro Cloning**: Clone voices from short 3s audio samples or video files.
  - **Voice Mixer**: Combine multiple voice profiles with granular weight control.
- **Production Engine**:
  - **True Streaming**: Real-time, line-by-line audio synthesis for long scripts.
  - **Instruction Brackets**: Support for emotional cues like `[whispered]` or `[sarcastic]`.
  - **Audio Effects**: Integrated EQ presets and algorithmic reverb.
- **Video Generation**:
  - **Scene Search**: AI-powered prompt suggestions based on script keywords.
  - **Narrated Video**: One-click generation of MP4s with audio and SRT subtitles.
- **System Management**:
  - **Unified Inventory**: One-click download and health checks for all models.
  - **Resource Monitor**: Real-time CPU, RAM, and GPU (VRAM) usage tracking.
  - **Audit Log**: Full transparency for every generation task.

## 🚀 Getting Started

### 1. Requirements
- Python 3.9+
- NVIDIA GPU (8GB+ VRAM recommended for Video)

### 2. Installation & Launch
The **Studio Launcher** handles everything: environment creation, CUDA detection, and dependency installation.

**Windows Users:**
Double-click `studio.bat` or run:
```powershell
.\studio.bat
```

**Linux/macOS Users:**
```bash
chmod +x studio-linux.sh
./studio-linux.sh
```

### 3. Usage
Navigate to: `http://localhost:8080`

## 🛠️ Tech Stack
- **Backend**: FastAPI, PyTorch (Qwen-TTS), LTX-Pipelines.
- **Frontend**: Vanilla JS (Modular ES6+), CSS3 (Technoid Brutalist).
- **Audio/Video**: Soundfile, Pydub, MoviePy, OpenCV.

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.
