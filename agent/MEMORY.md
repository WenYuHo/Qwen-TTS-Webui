# Agent DNA (Memory Bank)

> **MASTER FRAMEWORK:** [Conductor Framework](/conductor) | **SOURCE OF TRUTH:** [conductor/index.md](/conductor/index.md)

## 🧠 Core Grounding
This file contains the "High-Signal DNA" for any AI agent. Read it at the start of every session.
- **Project Structure:** [CODEBASE_MAP.md](CODEBASE_MAP.md) | [ARCHITECTURE.md](ARCHITECTURE.md)
- **Log of Decisions:** [DECISIONS.md](DECISIONS.md) | **Milestones:** [RECENT_MILESTONES.md](RECENT_MILESTONES.md)
- **Specialized Skills:** [../skills/skills.md](../skills/skills.md) (Load on-demand)

## 🚨 Critical Project Rules
1.  **Strict Tech Stack:** No React/Vue/Tailwind. Strictly Vanilla JS/CSS.
2.  **Design System:** Technoid Brutalist UI (Onyx #080808 + Volt #ccff00).
3.  **Mandatory TDD:** Write failing tests **before** implementation code.
4.  **No `print()`:** Use `logging` exclusively.
5.  **Pathing:** Always use `pathlib.Path` relative to project root.
6.  **Git Flow:** Use feature branches (`ralph/task-name`). Commit WIP before pulling.
7.  **Verification:** Every session must begin with `python tools/session_start.py`.

## 📋 Active Development Tracks (Mar 2026)
*Refer to [/conductor/tracks.md](/conductor/tracks.md) for full context.*
1.  **Sound Generation Quality**: Silence padding for ICL, Temperature presets.
2.  **Dubbing & S2S**: Hardening Voice Conversion and Dubbing APIs.
3.  **Testing & Reliability**: Increasing coverage, E2E browser tests.
4.  **Production Workflow**: Multi-format export, timeline views.

*To update: Keep this file under 50 lines. Move details to specialized files.*
