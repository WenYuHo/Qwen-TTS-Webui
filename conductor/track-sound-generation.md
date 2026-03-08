# Track: Sound Generation Performance & Quality

## Overview
- **Goal:** Systematically improve TTS voice generation quality, clarity, and performance across all voice types (preset, design, clone, mix).
- **Status:** ACTIVE
- **Owner:** Any Agent
- **Start Date:** 2026-03-05

---

## ⚠️ AGENT GUARDRAILS — READ FIRST

Every agent assigned to this track **MUST** follow these mandatory steps before writing code:

### Step 0: Memory Check (MANDATORY — DO THIS FIRST)
1. **Read** `agent/MEMORY.md` — understand current project state, folder structure, and core tenets
2. **Read** `agent/TASK_QUEUE.md` — check if your work overlaps with existing queue items
3. **Read** this track file — find the next `[ ]` task in the plan below
4. **Read** `conductor/index.md` — confirm you know the workflow and style sources

### Step 1: Understand the Rules
1. **Read** `conductor/workflow.md` — follow Standard Task Workflow phases (Red/Green/Refactor/Commit)
2. **Read** `conductor/code_styleguides/python.md` — Python conventions
3. **Read** `conductor/code_styleguides/javascript.md` — JS conventions  
4. **Read** `conductor/code_styleguides/html-css.md` — UI conventions (Technoid Brutalist)
5. **Read** `conductor/code_styleguides/agent-improvement.md` — Security, FastAPI routing, Pydantic V2

### Step 2: Verify Before Coding
- **Run tests first** to confirm a clean baseline: `python -m pytest tests/ -v --tb=short`
- **Check the environment**: read `.env` and `conductor/tech-stack.md` for dependencies

### Step 3: Work the Plan
- Pick the next `[ ]` task below, mark it `[~]`, follow TDD (Red→Green→Refactor), commit per `conductor/workflow.md`

---

## Phase 1: Voice Sample & Preview Quality 🎤

### Tasks

- [x] **1.1 — Curated Preview Text Pool**
- [x] **1.2 — Custom Preview Text (Backend)**
- [x] **1.3 — Custom Preview Text (Frontend)**
- [x] **1.4 — Rich Default Preview Sentences**
- [x] **1.5 — Clarity Instruct Hint**

---

## Phase 2: Voice Cloning Quality (ICL Mode) 🧬

### Tasks

- [x] **2.1 — ref_text Schema Support**
- [x] **2.2 — ICL Mode in PodcastEngine**
- [x] **2.3 — ref_text Frontend (Clone Tab)**
- [x] **2.4 — ref_text in Preview Endpoint**

---

## Phase 3: Advanced Generation Performance ⚡

### Tasks

- [x] **3.1 — Benchmark Baseline**
- [x] **3.2 — Prompt Caching Efficiency Audit**
- [x] **3.3 — Silence Padding for ICL (Anti-Bleed)**
- [x] **3.4 — Reference Audio Quality Validation**
- [x] **3.5 — Generation Temperature Presets**

---

## Phase 4: Multi-Segment Clarity & Consistency 📊

### Tasks

- [x] **4.1 — Per-Segment Quality Scoring**
- [x] **4.2 — Auto-Retry on Low Quality**
- [x] **4.3 — Cross-Segment Consistency Check**
- [x] **4.4 — Post-Processing Pipeline Enhancement**

---

## Phase 5: Testing & Verification ✅

### Tasks

- [x] **5.1 — Unit Tests for Preview Text Pool**
- [x] **5.2 — Unit Tests for ICL Mode Toggle**
- [x] **5.3 — Integration Test: Full Clone Workflow**
- [x] **5.4 — Update Existing Tests**

---

## Key Files Reference

| File | Purpose | Key Lines |
|------|---------|-----------|
| `src/backend/api/voices.py` | Preview endpoint, PREVIEW_TEXTS pool | L17-26 (texts), L77-101 (preview endpoint) |
| `src/backend/api/schemas.py` | SpeakerProfile, PodcastRequest, all schemas | L4-9 (SpeakerProfile), L27-35 (PodcastRequest) |
| `src/backend/api/generation.py` | Synthesis endpoints, `run_synthesis_task` | L34-78 (task runner), L101-146 (endpoints) |
| `src/backend/podcast_engine.py` | Core engine: generate_segment, generate_podcast | L210-271 (generate_segment), L349-516 (podcast) |
| `src/backend/qwen_tts/inference/qwen3_tts_model.py` | Model API | L390-515 (create_clone_prompt), L526-692 (generate_clone), L792-902 (custom_voice) |
| `src/backend/utils.py` | AudioPostProcessor, AuditManager, prune_dict_cache | L31-44 (prune), L119-232 (AudioPostProcessor) |
| `src/static/index.html` | UI layout | Temperature preset dropdown, settings area |
| `src/static/voicelab.js` | Voice lab JS | L6-69 (design), L71-140 (clone), L142-206 (mix) |
| `src/static/production.js` | Production JS | L5-132 (generatePodcast) |

---

## Recent Updates

### 2026-03-07: Advanced Quality & Reliability Completed
- Implemented Phase 3 & 4: silence padding for ICL, ref audio validation, temperature presets, per-segment quality scoring (SNR/clipping), auto-retry on low quality, voice drift detection, and enhanced post-processing (de-clicker, compressor).
- Completed Phase 5: comprehensive unit and integration tests for all new features.
- All 36 tests pass.
