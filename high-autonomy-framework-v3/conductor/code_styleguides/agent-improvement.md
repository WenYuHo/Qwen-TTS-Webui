# Agent Improvement & Automated Workflow

This guide defines the standards for AI agents (like Jules or Conductor) performing autonomous improvements or maintenance on this codebase.

## Architectural Conventions

- **FastAPI Modular Routing:** All new features must use `APIRouter` in `src/backend/api/`. Avoid growing `server.py`.
- **Pydantic V2:** Use `model_dump_json()` and `field_validator` (Pydantic V2) for all schemas.
- **Python Type Hints:** Mandatory for all API endpoints and core engine methods.
- **Security:** Always use `PodcastEngine._resolve_path` for file resolution to prevent directory traversal.

## Automated Workflow (Option 3)

When explicitly requested by the user for faster iterations, agents are authorized to push directly to the `main` branch.

### Workflow Steps:
1. `git checkout main`
2. `git pull origin main`
3. `git merge <feature-branch>` (or `git add .` if working directly on main)
4. `git commit -m "Jule automated update: <description>"`
5. `git push origin main`

## Style Guide (Technoid Brutalist)

For UI improvements, adhere to the "Technoid Brutalist" aesthetic:
- **Base Background:** Onyx (#080808) with subtle noise texture.
- **Accent Color:** Volt (#ccff00).
- **Borders:** 2px sharp solid borders (no radius).
- **Shadows:** Multi-layered, sharp drop shadows for depth.
- **Typography:** Monospace for technical data, high-contrast Sans-serif for UI labels.
