# Qwen-TTS Podcast Studio (v2.1) 🎙️

A standalone, professional web suite for Qwen-TTS production. Create stories, podcasts, and dialogues with custom voices and atmospheric background music.

## 🤖 For AI Agents

This repository follows the **Conductor Framework**. Before starting any work, AI agents MUST read the following:
- **Project Index:** [conductor/index.md](conductor/index.md)
- **Workflow & Rules:** [conductor/workflow.md](conductor/workflow.md)
- **Agent Style Guide:** [conductor/code_styleguides/agent-improvement.md](conductor/code_styleguides/agent-improvement.md)

Agents should always prioritize the definitions in `conductor/` as the single source of truth for architectural and stylistic decisions.

## ✨ Features

- **Professional Dashboard**: Clean 3-column layout (Speakers, Story Canvas, Production).
- **Hybrid Story Canvas**: Switch between a distraction-free **Draft** and a granular, blocks-based **Production** timeline.
- **Voice Studio**: 
  - **Voice Design**: Create voices from text descriptions.
  - **Voice Cloning**: Clone voices from short 3s audio samples.
- **Production Timeline**:
  - **Batch Synthesis**: One-click to generate your entire script.
  - **Timeline Recovery**: Autosave ensures your dialogue and audio segments survive page refreshes.
- **Studio Essentials**:
  - **BGM Mixing**: Layer your podcast with atmospheric moods (Mystery, Tech, Joy, Rain).
  - **Export/Import**: Backup and share your custom Speaker Library as JSON.
- **Standalone Power**: Private local virtual environment setup for zero-conflict dependency management.

## 🚀 Getting Started

### 1. Requirements
- Python 3.9+
- Existing Qwen-TTS models (referenced via `.env`)

### 2. Installation
Clone the repository and run the setup script to create a private environment and install AI libraries (Torch, etc.):
```bash
# Double-click or run:
setup_env.bat
```

### 3. Configuration
Copy `.env.example` to `.env` and point to your existing model directory:
```env
QWEN_MODELS_DIR=./models
```

### 4. Usage
Launch the studio:
```bash
start.bat
```
Navigate to: `http://localhost:8080`

## 🛠️ Tech Stack
- **Backend**: FastAPI, PyTorch (Qwen-TTS).
- **Frontend**: Vanilla JS (ES6+), CSS3 (Glassmorphism), HTML5.
- **Audio**: Soundfile, Pydub.

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.
