---
name: architect
description: Manages high-level system changes, database/schema updates, and large-scale refactors. Use when a task requires cross-cutting changes or updating core engine modules.
---

# Architect Skill

This skill provides guidance for modifying the core infrastructure of the project.

## 🏗️ Architectural Guidelines

### 1. Cross-Cutting Changes
- Use `codebase_investigator` to map all impacted files before making a change.
- Update `agent/CODEBASE_MAP.md` if a new directory or core module is added.
- Log major decisions in `agent/DECISIONS_LOG.md`.

### 2. Backend Design
- Strictly follow `FastAPI` async/await patterns.
- Use `BackgroundTasks` for long-running synthesis jobs.
- Maintain Pydantic V2 compatibility.

### 3. Engine Integrity
- Core logic lives in `src/backend/podcast_engine.py` or specialized `engines/`.
- Ensure all engine modules are modular and testable in isolation.
- Update `agent/ARCHITECTURE.md` if the system's "Current Architecture State" changes.

## 📋 Target Files
- `src/backend/`
- `agent/DECISIONS_LOG.md`
- `agent/ARCHITECTURE.md`
- `agent/CODEBASE_MAP.md`
