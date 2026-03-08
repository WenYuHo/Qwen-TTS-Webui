# Agent Protocols (DNA)

> **MASTER FRAMEWORK:** [Conductor Framework](/conductor) | **SOURCE OF TRUTH:** [conductor/index.md](/conductor/index.md)

## 1. ⚡ STARTUP
**Every session MUST begin with:**
`python tools/session_start.py`
*(This re-hydrates your context with git status, active tasks, and recent decisions.)*

## 2. 🧠 CORE DNA
- **Project Context:** [agent/MEMORY.md](agent/MEMORY.md) (Read this first)
- **Architecture:** [agent/ARCHITECTURE.md](agent/ARCHITECTURE.md)
- **Decisions Log:** [agent/DECISIONS.md](agent/DECISIONS.md)

## 3. 🛠️ WORKFLOW (Plan -> Act -> Verify)
1.  **Reserve Task:** `python tools/reserve.py` (Locks next task)
2.  **Activate Skill:** [skills/skills.md](skills/skills.md) (Load specialized instructions)
3.  **Implement:**
    - **Strict TDD:** Write failing test -> Write code -> Pass test.
    - **No `print()`:** Use `logging`.
    - **Atomic Commits:** `git commit -m "feat: ..."`
4.  **Verify:** `pytest` && `python tools/pre_commit.py`

## 4. 🚀 COMPLETION
1.  **Finalize:** `python tools/finish.py` (Updates logs and task queue)
2.  **Push:** `git push origin <branch_name>`

*Keep this file under 50 lines. It is the only file you need to read to start.*
