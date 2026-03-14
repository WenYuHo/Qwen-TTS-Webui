# Agent DNA (Memory Bank)

> **MASTER FRAMEWORK:** [Conductor Framework](/conductor) | **SOURCE OF TRUTH:** [conductor/index.md](/conductor/index.md)

## 🧠 Core Grounding
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md) | **Codebase Map:** [CODEBASE_MAP.md](CODEBASE_MAP.md)
- **Decisions:** [DECISIONS.md](DECISIONS.md) *(read only when making architectural choices)*
- **Lessons:** [LESSONS.md](LESSONS.md) *(read at startup, append after each task)*
- **Skills:** [../skills/skills.md](../skills/skills.md) *(load on-demand per task phase)*

## 🚨 Coding Standards (Single Source of Truth)
1.  **Tech Stack:** Vanilla JS/CSS + Python FastAPI. No React/Vue/Tailwind. No Webpack/Vite.
2.  **Design System:** Technoid Brutalist UI (Onyx `#080808` + Volt `#ccff00`).
3.  **TDD:** Write failing tests → implement → pass tests → refactor. No exceptions.
4.  **Logging:** Use `logging` exclusively. No `print()` in production code.
5.  **Pathing:** Always use `pathlib.Path` relative to project root.
6.  **Git Flow:** Feature branches (`ralph/task-name`). Commit WIP before pulling.
7.  **Python:** Pydantic V2 (`model_dump_json`, `field_validator`). Type hints on all API endpoints.
8.  **FastAPI:** New endpoints use `APIRouter` in `src/backend/api/`. Never grow `server.py`.
9.  **Security:** Use `PodcastEngine._resolve_path` for all file resolution.
10. **Audio I/O:** Prefer `soundfile` over `librosa`. Only use `librosa` for spectral analysis.

## 🚫 Negative Constraints (Do NOT)
- Do NOT add npm, Webpack, Vite, or any JS build tooling.
- Do NOT use `librosa` for simple file I/O — use `soundfile`.
- Do NOT grow `server.py` — create new `APIRouter` modules.
- Do NOT assume `ffmpeg`/`sox` are on system PATH — use `config.py` resolution.
- Do NOT read `track-*.md`, `workflow.md`, or `DECISIONS.md` unless the current task requires it.
- Do NOT log `.env` values or secrets.

## 📋 Active Tracks (Mar 2026)
*See [/conductor/tracks.md](/conductor/tracks.md). Load track files on-demand only.*

## ⚡ Token Discipline
- Load skill files on-demand per task phase. Never read all skills at once.
- Summarize findings into compact notes. Drop raw file contents from context when done.
- **Context Compaction:** If context feels >50% full, write a `SCRATCHPAD.md` summary and start fresh.

*Keep this file under 40 lines. Move details to specialized files.*
