# Agent Protocols (DNA) v2

> **SOURCE OF TRUTH:** [conductor/index.md](conductor/index.md)

## 1. ⚡ BOOT (every session)
1. `git pull --rebase --autostash`
2. `python tools/session_start.py`
3. Read [agent/MEMORY.md](agent/MEMORY.md) — the **ONLY** file you need at startup.

## 2. 🛠️ WORK (Plan → Act → Verify)
1.  **Reserve Task:** `python tools/reserve.py`
2.  **Load Skill:** Read the relevant [skill](skills/skills.md) for this task phase. Do NOT read all skills.
3.  **Implement:** Follow rules in [MEMORY.md](agent/MEMORY.md). Use `agent-browser` for UI verification.
4.  **Verify:** `pytest; python tools/pre_commit.py`
5.  **Finish:** `python tools/finish.py`
6.  **Push:** `git push origin <branch>`

## 3. 🧠 TOKEN BUDGET
- **NEVER** eagerly read large docs (`workflow.md`, `track-*.md`, `DECISIONS.md`).
- **ONLY** load skill files when entering that specific task phase.
- Read `DECISIONS.md` only when making an architectural choice.
- If context feels > 50% full: summarize findings into notes, drop raw file contents.

## 4. 🔄 SELF-IMPROVE (after every task)
1. What went wrong? (wasted tokens, wrong approach, test failures, confusion)
2. Append a 1-line lesson → [agent/LESSONS.md](agent/LESSONS.md)
3. If a rule in MEMORY.md caused the problem → fix it now.

## 5. 🤖 SYMPHONY (multi-agent only)
- Read [agent/MANDATE.md](agent/MANDATE.md) for swarm coordination rules.
- Update status: `python tools/sync_live.py "<agent>" "<status>" "<task>" "<pct>"`

*This file is the boot loader. All coding rules live in MEMORY.md. Keep this under 40 lines.*
