# Contributing to Qwen-TTS Podcast Studio

Welcome! This project follows a highly structured architectural and stylistic framework to ensure stability and high performance. Whether you are a human developer or an AI agent, please adhere to the following guidelines.

## 1. The Conductor Framework

All development is driven by the **Conductor Framework** located in `/conductor`.
- **Atomic Tasks:** No work should be performed without a corresponding entry in a `plan.md` or the `TASK_QUEUE.md`.
- **TDD Requirement:** Core engine changes must include or update relevant tests in `/tests`.
- **Source of Truth:** Always refer to `conductor/index.md` for the latest project state and roadmap.

## 2. Technoid Brutalist Design System

The UI follows a specific **Technoid Brutalist** aesthetic. When adding new components, use these design tokens:

- **Color Palette:**
  - Background: Onyx (#080808)
  - Accent: Volt (#ccff00)
  - Card: Deep Gray (#111111)
  - Border: Volt-Glow (rgba(204, 255, 0, 0.3))
- **CSS Utility Classes:**
  - `.card-brutalist`: Sharp 2px Volt borders with multi-layered shadows.
  - `.volt-text`: Text using the accent color with a subtle glow.
  - `.label-industrial`: Monospace, uppercase, tracked-out labels for controls.
  - `.status-val`: Bold, monospace readouts for technical data.

## 3. Modular Frontend Architecture

The frontend is modularized using ES Modules in `src/static/`.
- **`app.js`**: Main entry point and state management.
- **`voicelab.js`**: Voice design, cloning, and mixing logic.
- **`production.js`**: Project Studio and podcast generation logic.
- **`system.js`**: Model inventory, settings, and hardware monitoring.
- **`assets.js`**: Media asset management.
- **`ui_components.js`**: Shared UI elements like modals and notifications.

**Rule:** Avoid adding large logic blocks to `index.html`. Export functions from modules and bind them to the `window` object in `app.js` only if needed for HTML event handlers.

## 4. Backend Standards

- **Modular Routing:** All API endpoints must reside in `src/backend/api/`.
- **Engine Logic:** Core synthesis and processing logic must be in `src/backend/engines/` or `src/backend/podcast_engine.py`.
- **Type Hinting:** Mandatory for all public methods and API schemas.
- **Pydantic V2:** Use Pydantic V2 conventions (`model_dump()`, etc.) for all data validation.

## 5. Autonomous Improvement

This repository includes an **Autonomous Improvement System** triggered daily.
- Agents must log their changes in `agent/IMPROVEMENT_LOG.md`.
- Tasks are prioritized in `agent/TASK_QUEUE.md`.
- Agents have full autonomy for non-destructive improvements but must follow the Conductor Plan.

Thank you for helping evolve the Qwen-TTS Podcast Studio!
