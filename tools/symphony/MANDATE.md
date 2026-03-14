# SYMPHONY ORCHESTRATION PROTOCOL (v7)

## 1. 🎭 ROLES

| Role | Responsibility | Context Layers |
|:---|:---|:---|
| Manager | Task assignment, review gate, conflict resolution | L0 + L1 |
| Worker | Execute assigned task, report status | L0 + L1 + L2 |

## 2. 📡 STATE MACHINE (per task)

```
IDLE → RESERVED → IN_PROGRESS → REVIEW → [APPROVED | REJECTED] → DONE
```

- Workers transition: `IDLE → RESERVED → IN_PROGRESS → REVIEW`
- Manager transitions: `REVIEW → APPROVED/REJECTED → DONE`
- Rejected tasks return to `IN_PROGRESS` with specific feedback

## 3. 🔄 SYNC PROTOCOL
- **Workers:** `python tools/sync_live.py "<agent>" "<status>" "<task>" "<pct>"`
- **Manager:** Polls `agent/SYMPHONY_LIVE.md` for status updates
- **Conflicts:** First-to-push wins. Loser rebases. If too complex → HALT and request human.

## 4. 🔍 REVIEW GATE (Manager Only)
Before approving ANY Worker task:
1. `git diff` on the Worker's branch
2. Check against `agent/MEMORY.md` coding standards
3. Violations → reject with specific feedback in `TASK_QUEUE.md`
4. Clean → approve and merge

## 5. 🧬 SKILL LOADING
Load skills on-demand (L2). Do NOT read all skills at startup.
- **Testing/TDD:** `skills/tester/SKILL.md`
- **Architecture:** `skills/architect/SKILL.md`
- **Context/Memory:** `skills/dna-evolution/SKILL.md`

## 6. 📦 CONTEXT COMPACTION (Workers)
When context >50% full during a long task:
1. Write summary to `SCRATCHPAD.md` in the worktree
2. Drop raw file contents from context
3. Continue from scratchpad summary

## 7. 🧠 META-REFLECTION
- **Manager:** If Workers struggle, rewrite these instructions or `symphony_start.py`
- **Worker:** Write `[?] CLARIFICATION_NEEDED` in `TASK_QUEUE.md` if confused
- **After each task:** Append lesson to `agent/LESSONS.md`
