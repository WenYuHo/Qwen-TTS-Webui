# Symphony: Multi-Agent Orchestration

> **Portable infrastructure layer.** This folder can be copied to any project that needs multi-agent coordination.

## What's Here

| File | Purpose |
|:---|:---|
| `MANDATE.md` | Orchestration protocol (roles, state machine, sync, review gates) |
| `ralph/state.json` | Ralph autonomous loop state |

## How to Use

1. Copy this `tools/symphony/` folder into your project
2. Add a one-line reference in your project's `AGENTS.md`:
   ```markdown
   ## SYMPHONY (multi-agent only)
   See [tools/symphony/MANDATE.md](tools/symphony/MANDATE.md)
   ```
3. Create worktrees for workers: `git worktree add worker-1 main`
4. Launch the symphony with your project's `symphony_start.py`

## Dependencies

- `tools/sync_live.py` — status sync script (create per-project)
- `symphony_start.py` — launcher (create per-project, lives in worktrees)
- `agent/SYMPHONY_LIVE.md` — live status board (auto-created by sync_live)
