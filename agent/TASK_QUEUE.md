# Task Queue: Autonomous Improvement

## Prioritized Backlog

### Tier 1: Organization & Cleanup (High Priority)
1. [AWAITING APPROVAL] MOVE: Consolidate all root-level `update_*.py` scripts into `scripts/archive/`.
2. [AWAITING APPROVAL] MOVE: Consolidate root-level `verify_*.py` scripts (except `verify_setup.py`) into `scripts/verification/`.
3. [AWAITING APPROVAL] DELETE: Remove deprecated `generate_previews.py` from root.
4. [AWAITING APPROVAL] MOVE: Move `projects/` and `shared_assets/` to a new `data/` or `storage/` root directory to separate code from user data.
5. Create missing `README.md` for `src/backend/qwen_tts/core/`.

### Tier 2: Documentation Gaps
1. Document the `TaskManager` class in `src/backend/task_manager.py`.
2. Add type hints to `src/backend/podcast_engine.py` methods.
3. Update `conductor/product.md` to reflect the reconciled "Technoid Brutalist" vs "Classic Studio" design direction.

### Tier 3: Code Quality
1. Refactor `src/static/app.js` to extract large UI-rendering functions into smaller, modular files.
2. Standardize error handling in `src/backend/api/voices.py` to use the centralized logger consistently.

## Awaiting Human Feedback
- Should we move `setup_env.sh` and `start.sh` into a `bin/` or `scripts/` folder? (Standard practice vs ease of use).
