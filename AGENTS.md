# Agent Protocols (DNA) v3

> **SOURCE OF TRUTH:** [conductor/index.md](conductor/index.md)

## 1. ⚡ BOOT (automated)
1. `git pull --rebase --autostash`
2. `python tools/session_start.py` (now auto-run by agents)
3. Read **[agent/MEMORY.md](agent/MEMORY.md)** — your only startup read.

## 2. 🧠 CONTEXT LAYERS (load only what you need)

| Layer | When to Load | File |
|:---|:---|:---|
| L0: Identity | Always (via MEMORY.md) | `agent/MEMORY.md` |
| L1: Task | When starting a task | `agent/TASK_QUEUE.md` |
| L2: Skill | When entering a task phase | `skills/<name>/SKILL.md` |
| L3: Track | When task references a track | `conductor/track-*.md` |
| L4: History | When making architectural choices | `agent/DECISIONS.md` |

**NEVER** read L2–L4 files speculatively. Only load when the current task demands it.

## 3. 🛠️ WORK (Plan → Act → Verify)
1. Reserve: `python tools/reserve.py`
2. Load Skill (L2) for this task phase. Do NOT read all skills.
3. Implement: Follow rules in MEMORY.md. Use `agent-browser` for UI work.
4. Verify: `pytest; python tools/pre_commit.py`
5. Finish: `python tools/finish.py`
6. Push: `git push origin <branch>`

## 4. 🔄 SELF-IMPROVE (after every task)
1. What went wrong? (wasted tokens, wrong approach, test failures, confusion)
2. Append 1-line lesson → [agent/LESSONS.md](agent/LESSONS.md)
3. If a rule in MEMORY.md caused confusion → fix it *now*

## 5. 🤖 SYMPHONY (multi-agent only)
- **Launch:** Run `symphony.bat` or `python symphony_start.py` from root.
- **Protocol:** Read [tools/symphony/MANDATE.md](tools/symphony/MANDATE.md) for orchestration protocol.
- **Sync:** Update status: `python tools/sync_live.py "<agent>" "<status>" "<task>" "<pct>"`

*Boot loader only. All coding rules live in MEMORY.md. ≤45 lines.*
