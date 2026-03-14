# Context Engineering Guide

> This guide defines the **context layer system** used by all agents in this project.
> Reference: [AGENTS.md](../../AGENTS.md) §2

## Layer Definitions

| Layer | Name | Contents | Lifecycle |
|:---|:---|:---|:---|
| **L0** | Identity | `agent/MEMORY.md` — coding rules, constraints, tech stack | Always loaded at startup |
| **L1** | Task | `agent/TASK_QUEUE.md` — current task details | Loaded when reserving a task |
| **L2** | Skill | `skills/<name>/SKILL.md` — phase-specific instructions | Loaded when entering a task phase |
| **L3** | Domain | `conductor/track-*.md`, `product.md`, `workflow.md` | Loaded when task references a specific domain |
| **L4** | History | `agent/DECISIONS.md`, `agent/EVOLUTION.md` | Loaded only for architectural decisions |

## Loading Triggers

- **L0:** Automatic. `session_start.py` reminds agents this is pre-loaded.
- **L1:** When `python tools/reserve.py` assigns a task.
- **L2:** When the task enters a specific phase (testing, architecture, DNA evolution).
- **L3:** When the task description references a conductor track or domain knowledge.
- **L4:** When making a decision that could conflict with past architectural choices.

## Compaction Rules

When your context window feels >50% full:

1. **Summarize:** Write a `SCRATCHPAD.md` in your worktree with key findings.
2. **Drop:** Remove raw file contents from your active context.
3. **Continue:** Work from the scratchpad summary, not the original files.
4. **Signal:** Log `[COMPACTED]` in your sync status so the Manager knows.

## Anti-Patterns (Do NOT)

| Anti-Pattern | Why It Wastes Tokens |
|:---|:---|
| Reading all `track-*.md` at startup | Each track is 20K+ bytes. Load only the one your task needs. |
| Reading `DECISIONS.md` without an architectural task | History is only useful when making structural choices. |
| Loading all skills preemptively | Skills are phase-specific. A testing phase doesn't need architect skills. |
| Reading `workflow.md` during routine coding | The workflow is for process questions, not coding rules. |
| Keeping raw file contents after extracting info | Summarize and drop. Raw content eats context fast. |

## Context Budget Targets

| File | Max Size | Budget |
|:---|:---|:---|
| `AGENTS.md` | ≤45 lines | Boot loader only |
| `MEMORY.md` | ≤45 lines | All coding rules |
| `MANDATE.md` | ≤45 lines | Orchestration only |
| `LESSONS.md` | ≤30 entries | Prune oldest when exceeded |
| `workflow.md` | ≤120 lines | Process reference |
