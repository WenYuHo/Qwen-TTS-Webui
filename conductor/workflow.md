# Project Workflow

## Hybrid Agent Coordination & PR Protocol

When multiple agents work on the same repository, follow these synchronization rules.

### 1. The Pull-First Rule
- **Mandatory:** `git pull --rebase --autostash` at the start of every session or task.
- If local changes block a rebase, commit them as WIP first (`git commit -m "chore: WIP local changes"`).

### 2. Feature Branch Requirement
- **NEVER** commit directly to `main`.
- Every task uses a unique feature branch (e.g., `ralph/task-name`).
- When a user initiates an autonomous task, this constitutes explicit permission to stage and commit to the feature branch.
- Once tests pass, push the branch and open a PR.

### 3. PR Polling & Fix Loop
- After opening a PR, monitor CI results (`gh pr view`).
- If CI fails or PR is rejected: read feedback, apply fixes on the same branch, re-push.
- A task is only "Done" when the PR is merged into `main`.

### 4. Conflict Resolution
- Attempt automatic resolution. If too complex → stop and ask for human intervention.

### 5. Human-In-The-Loop Gate
- For **breaking changes** or **architectural shifts**: pause and ask the user before proceeding.
- For ambiguous requirements: write `[?] CLARIFICATION_NEEDED` in `TASK_QUEUE.md`.

---

## Task Workflow

### Standard Task Lifecycle
1. **Select Task:** Choose the next available task from `agent/TASK_QUEUE.md`
2. **Mark In Progress:** Change `[ ]` to `[~]`
3. **Write Failing Tests (Red):** Create tests that define expected behavior. Confirm they fail.
4. **Implement (Green):** Write minimum code to make tests pass. Confirm all pass.
5. **Refactor:** Improve clarity and remove duplication. Rerun tests.
6. **Verify Coverage:** `pytest --cov=src --cov-report=html` → target >80% on new code.
7. **Document Deviations:** If implementation differs from tech stack: STOP, update `tech-stack.md`, then resume.
8. **Commit:** `<type>(<scope>): <description>` format.
9. **Attach Summary:** `git notes add -m "<summary>" <commit_hash>`
10. **Update Plan:** Mark task `[x]` in the queue with first 7 chars of commit SHA.

### Quality Gates
Before marking any task complete:
- [ ] All tests pass
- [ ] Code coverage >80%
- [ ] Follows [code style guides](code_styleguides/)
- [ ] Public functions documented (docstrings/JSDoc)
- [ ] Type hints enforced
- [ ] No linting errors
- [ ] Documentation updated if needed

---

## Development Commands

### Setup
```bash
python tools/session_start.py       # Verify env, show active tasks
pip install -r requirements.txt     # Install dependencies
```

### Daily Development
```bash
python src/backend/server.py        # Start FastAPI dev server
pytest                              # Run all tests
pytest --cov=src --cov-report=html  # Coverage report
python tools/pre_commit.py          # Pre-commit checks
```

### Before Committing
```bash
python tools/pre_commit.py          # Lint, format, type check
pytest                              # Confirm all tests pass
```

---

## Commit Message Format

```
<type>(<scope>): <description>
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

```bash
# Examples
git commit -m "feat(api): Add voice cloning endpoint"
git commit -m "fix(engine): Correct BGM ducking threshold"
git commit -m "test(api): Add voices endpoint coverage"
```

## Definition of Done

A task is complete when:
1. Code implemented to specification
2. Unit tests written and passing (>80% coverage)
3. Documentation complete if applicable
4. Code passes all linting and static analysis
5. Implementation notes added to task queue
6. Changes committed with proper message and git note attached

## Continuous Improvement

- Document lessons in `agent/LESSONS.md`
- Optimize for user happiness
- Keep things simple and maintainable
