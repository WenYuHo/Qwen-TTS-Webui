# SYMPHONY AGENT MANDATE (v5.1)

## 🧬 SKILL SYSTEM
You are AUTHORIZED to use the project's internal skills. Load them on-demand:
- **Testing/TDD**: `skills/tester/SKILL.md`
- **Architectural**: `skills/architect/SKILL.md`
- **Context/Memory**: `skills/dna-evolution/SKILL.md`
Reading `skills/skills.md` at the start of every task is MANDATORY.

## 🧠 META-REFLECTION
1. **Self-Correction**: If you (the Manager) see Workers struggling, rewrite these instructions or `symphony_start.py`.
2. **Confused Workers**: If you are a Worker and confused, write `[?] CLARIFICATION_NEEDED` in `agent/TASK_QUEUE.md` immediately.

## ⚡ GPU SAFETY (8GB VRAM)
- Your 2070 Super has 8GB VRAM. 
- ALWAYS check and respect the GPU Token protocol in `agent/GPU.lock`.

## 🏗️ EXECUTION LOOP
1. **RESERVE**: Mark task as reserved in `agent/TASK_QUEUE.md`.
2. **PLAN**: Write a brief strategy in your thought process.
3. **ACT**: Execute changes using TDD.
4. **VERIFY**: Run tests and session snapshots.
5. **SYNC**: Update queue and memory.
