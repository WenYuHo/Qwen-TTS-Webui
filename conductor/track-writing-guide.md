# Track Writing Guide

> **Purpose:** This guide teaches agents how to write implementation-ready conductor tracks. Every new track MUST follow this format.

---

## 🚨 Rule #1: Source-First, Always

Before writing any task, **read the source code** you're referencing:
1. Use `view_file_outline` to get function signatures
2. Use `view_file` to read the specific lines you'll reference
3. Use `grep_search` to find integration points
4. **Cite exact line numbers and function names** in your tasks

> A task that says "modify `generate_segment`" is useless. A task that says "modify `generate_segment()` at line 241, in the clone branch where `x_vector_only_mode` is set" is actionable.

---

## Track File Structure

Every track file follows this structure:

```markdown
# Track: [Name]

## Overview
- **Goal:** [One sentence]
- **Status:** PLANNED | IN_PROGRESS | COMPLETE
- **Owner:** Any Agent
- **Start Date:** TBD
- **Models:** [List relevant models and their capabilities]

---

## ⚠️ AGENT GUARDRAILS — READ FIRST

### Step 0: Memory Check (MANDATORY)
1. **Read** `agent/MEMORY.md`
2. **Read** `agent/TASK_QUEUE.md`
3. **Read** this track file
4. **Read** `conductor/workflow.md`

### Step 1: Understand the Code
1. **Read** [list exact source files agent must read before coding]
2. **Read** [list style guides or docs]

---

## Phase N: [Phase Name] [Emoji]

> **Why:** [Why this phase matters — motivation, not just description]

### Current Architecture (from `file.py` L##-##):
```lang
[Show the CURRENT code the agent will be modifying]
```

### Tasks

- [ ] **N.M — Task Name**
  [Detailed implementation with code snippets...]
  **Acceptance:** [Concrete pass/fail test]
```

---

## Task Detail Requirements

### ❌ BAD — Not Detailed Enough

```markdown
- [ ] **1.1 — Add language detection**  
  Detect the source language from audio.  
  **Files:** `podcast_engine.py`  
  **Acceptance:** Language is detected.
```

### ✅ GOOD — Implementation-Ready

```markdown
- [ ] **1.1 — Add language detection**

  **Step 1: Modify `transcribe_audio()` at line 119 to return language:**
  ```python
  def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
      result = model.transcribe(source_path)
      return {
          "text": result.get("text", ""),
          "language": result.get("language", "unknown"),
      }
  ```

  **⚠️ Breaking change:** Currently returns `str`. Update callers:
  ```python
  # In dub_audio (L518):
  result = self.transcribe_audio(audio_path)
  text = result["text"]
  ```

  **Step 2: Add endpoint in `generation.py`:**
  ```python
  @router.post("/detect-language")
  async def detect_language(file: UploadFile = File(...)):
      # ... code ...
  ```

  **Acceptance:** Upload audio → API returns `{"language": "en"}`.
```

---

## Checklist For Every Task

Each task MUST include:

| Element | Required | Example |
|---------|----------|---------|
| **Step-by-step instructions** | ✅ | "Step 1: Add model → Step 2: Wire endpoint → Step 3: Add UI" |
| **Code snippets** | ✅ | Ready-to-copy Python/JS/HTML/CSS |
| **Exact file paths** | ✅ | `src/backend/api/voices.py` |
| **Line numbers** | ✅ where modifying | "at line 241, in the clone branch" |
| **Breaking changes** | ✅ if any | "⚠️ `transcribe_audio()` return type changes" |
| **Schema changes** | ✅ if any | Exact Pydantic model additions |
| **Frontend wiring** | ✅ if UI involved | JS event handlers + HTML elements |
| **Model API reference** | ✅ if using TTS/LTX | `instruct` strings, kwargs, return shapes |
| **Acceptance criteria** | ✅ | "Upload audio → UI shows 'Detected: English'" |
| **Dependencies** | ✅ if any | "Requires Task 1.2 to be completed first" |

---

## Key Files Reference Table

Every track ends with a Key Files Reference table:

```markdown
| File | Purpose | Key Lines |
|------|---------|-----------|
| `src/backend/api/voices.py` | Voice API endpoints | L14 (`preview`), L77 (`library CRUD`) |
| `src/static/voicelab.js` | Frontend voice management | `loadLibrary()`, `toggleFavorite()` |
```

**Include:**
- File path
- What the file does (in context of this track)
- Key functions or line ranges
- `[NEW]` / `[MODIFY]` / `[DELETE]` markers

---

## Model API Quick Reference

If the track uses Qwen3-TTS or LTX, end with a quick reference:

```markdown
### Qwen3 TTS Quick Reference
```python
# Preset voice:
wavs, sr = model.generate_custom_voice(text, speaker="Aiden", language="en", instruct="...")

# Voice design:
wavs, sr = model.generate_voice_design(text, description="A deep male voice")

# Voice clone (ICL):
prompts = model.create_voice_clone_prompt(ref_audio=path, ref_text=text, x_vector_only_mode=False)
wavs, sr = model.generate_voice_clone(text, voice_clone_prompt={...})

# instruct parameter examples:
instruct="happy, cheerful, upbeat delivery"
instruct="slow, deliberate, measured pace"
instruct="preserve original rhythm, pacing, and emphasis"
```
```

---

## Phase Ordering Rules

1. **Phase 1** = Backend schema + core logic
2. **Phase 2** = API endpoints + integration
3. **Phase 3** = Frontend UI + wiring
4. **Phase 4** = Polish, optimization, edge cases

Each phase should be **independently shippable** — Phase 1 can be completed and tested before starting Phase 2.

---

## After Writing a Track

1. Register it in `conductor/tracks.md`
2. Add backlog items to `agent/TASK_QUEUE.md`
3. Update `agent/MEMORY.md` with the new track
4. Self-review: Can an agent with NO prior context complete Task 1.1 from this track alone?
