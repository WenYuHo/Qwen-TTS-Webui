# SYMPHONY AGENT MANDATE (v6)

## 🧬 SKILL SYSTEM
Load skills on-demand. Do NOT read all skills at startup.
- **Testing/TDD**: `skills/tester/SKILL.md`
- **Architectural**: `skills/architect/SKILL.md`
- **Context/Memory**: `skills/dna-evolution/SKILL.md`

## 🧠 META-REFLECTION
1. **Self-Correction**: If you (the Manager) see Workers struggling, rewrite these instructions or `symphony_start.py`.
2. **Confused Workers**: If you are a Worker and confused, write `[?] CLARIFICATION_NEEDED` in `agent/TASK_QUEUE.md` immediately.
3. **After each task**: Append a 1-line lesson to `agent/LESSONS.md`.

## ⚡ GPU SAFETY (8GB VRAM)
- ALWAYS check and respect the GPU Token protocol in `agent/GPU.lock`.

## 🏗️ EXECUTION LOOP
1. **RESERVE**: `python tools/reserve.py`
2. **PLAN**: Write a brief strategy. Load the relevant skill file.
3. **ACT**: Execute changes using TDD. Follow rules in `agent/MEMORY.md`.
4. **VERIFY**: `pytest; python tools/pre_commit.py`
5. **SYNC**: `python tools/finish.py` → append lesson → push.

## 🔍 REVIEW GATE (Manager Only)
Before marking ANY Worker task as complete, the Manager MUST:
1. Read the Worker's changed files (`git diff` on their worktree branch).
2. Check against `agent/MEMORY.md` coding standards and negative constraints.
3. If violations found → reject with specific feedback in `TASK_QUEUE.md`.
4. If clean → approve and merge the Worker's branch.

## 📦 CONTEXT COMPACTION (Workers)
When your context window feels >50% full during a long task:
1. Write a summary of your current findings to a `SCRATCHPAD.md` in the worktree.
2. Drop raw file contents from your context.
3. Continue working from the scratchpad summary.
This prevents infinite loops and context drift in long-running sessions.
