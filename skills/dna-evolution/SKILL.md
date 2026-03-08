---
name: dna-evolution
description: Refines the agent's own instructions, memory, and DNA files to ensure context efficiency and project alignment. Use when major architectural changes occur, when MEMORY.md exceeds 50 lines, or when recurring misunderstandings are identified.
---

# DNA Evolution

This skill is used to maintain the "Self-Correction" loop of the autonomous agent.

## 🧬 Evolution Protocol

### 1. Signal Identification
Trigger this workflow if:
- `agent/MEMORY.md` is too verbose (>50 lines).
- The agent repeatedly fails to follow a specific rule in `agent/MEMORY.md`.
- A "Track" in `/conductor` reaches a major milestone (e.g., Phase 1 Completion).

### 2. Information Pruning
- **MOVE** technical details (ports, color codes, API paths) to `agent/ARCHITECTURE.md`.
- **MOVE** historical context to `agent/RECENT_MILESTONES.md`.
- **KEEP** only the most critical "Rules of Survival" in `agent/MEMORY.md`.

### 3. Rule Refinement
If a rule is ambiguous, rewrite it to be imperative and concise.
- *Bad:* "We should try to use pathlib because it is more modern."
- *Good:* "STRICT RULE: Use `pathlib.Path` relative to root for all file operations."

### 4. Verification
After updating any DNA file, run `python tools/session_snapshot.py` to ensure the snapshot still captures the essential state.

## 📋 Target Files
- `agent/MEMORY.md` (Primary DNA)
- `agent.md` (Execution Protocol)
- `agent/ARCHITECTURE.md` (Technical Reference)
- `agent/RECENT_MILESTONES.md` (Historical Reference)
