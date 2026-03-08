# Qwen-TTS AI Entry Point

> **MISSION**: Autonomous audio production studio (v2.1)

## 🗺️ Codebase Map
- `src/backend/`: FastAPI API & Engine logic
- `src/static/`: Vanilla JS/CSS Frontend
- `tests/`: TDD & E2E (Playwright)
- `bin/`: Local ffmpeg/sox binaries

## 🧬 Agent Protocols
1.  **Read DNA**: [AGENTS.md](AGENTS.md)
2.  **Start Session**: `python tools/session_start.py`
3.  **Reserve Task**: `python tools/reserve.py`
4.  **Specialized Rules**: [skills/skills.md](skills/skills.md)
5.  **Finish Task**: `python tools/finish.py`

## 🚨 Constraints
- **Stack**: No React/Vue/Tailwind.
- **Style**: Technoid Brutalist UI.
- **TDD**: Write failing test before code.
- **Log**: No `print()` in production.

*Optimized for token efficiency. For human-readable details, see README.md.*
