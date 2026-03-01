# Folder Structure Proposal

The following structure aims to clean up the root directory and organize files by their responsibility.

## Proposed Structure

```text
.
├── src/                    # All source code
│   ├── backend/            # FastAPI, Logic, Engines
│   └── static/             # Frontend assets
├── scripts/                # Utility and maintenance scripts
│   ├── verification/       # verify_*.py
│   └── archive/            # update_*.py, old scripts
├── data/                   # Dynamic user data (not in git)
│   ├── projects/           # Moved from root/projects
│   └── shared_assets/      # Moved from root/shared_assets
├── tests/                  # All test suites
├── conductor/              # Project management & guidelines
├── .jules/                 # Agent instructions
├── agent/                  # Autonomous improvement state
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
├── setup_env.sh            # Keep at root for visibility
└── start.sh                # Keep at root for visibility
```

## Move Mapping

| File | Proposed Location | Risk | Note |
| :--- | :--- | :--- | :--- |
| `projects/*` | `data/projects/` | Medium | Requires updating paths in `src/backend/api/projects.py` and `shared.js`. |
| `shared_assets/*` | `data/shared_assets/` | Medium | Requires updating paths in `src/backend/api/assets.py`. |
| `update_*.py` | `scripts/archive/` | Low | Maintenance scripts, safe to move. |
| `verify_model_*.py` | `scripts/verification/` | Low | Safe to move. |
| `verify_setup.py` | `scripts/verification/` | Medium | Referenced by `start.sh`. Need to update `start.sh`. |

## Safety Status
- **Auto-move safe:** No files are marked as auto-move safe in the bootstrap phase. All moves require [AWAITING APPROVAL] status in `TASK_QUEUE.md` to be cleared by a human.
