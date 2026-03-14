# Project Workflow

## Guiding Principles

1. **The Plan is the Source of Truth:** All work must be tracked in `plan.md`
2. **The Tech Stack is Deliberate:** Changes to the tech stack must be documented in `tech-stack.md` *before* implementation
3. **Test-Driven Development:** Write unit tests before implementing functionality
4. **High Code Coverage:** Aim for >80% code coverage for all modules
5. **User Experience First:** Every decision should prioritize user experience
6. **Non-Interactive & CI-Aware:** Prefer non-interactive commands. Use `CI=true` for watch-mode tools

## Hybrid Agent Coordination & PR Protocol

When multiple agents work on the same repository, they must follow these synchronization rules.

### 1. The Pull-First Rule
- **Mandatory:** Execute `git pull --rebase --autostash` at the start of every session or task.
- If local changes exist that block a rebase, the agent must **commit them as a WIP** (`git commit -m "chore: WIP local changes"`) before pulling.

### 2. Feature Branch Requirement
- Agents **MUST NOT** commit directly to the `main` branch.
- Every task must be performed on a unique feature branch (e.g., `ralph/task-name`).
- Once the task is complete and tests pass, push the branch and open a Pull Request (PR).

### 3. The PR Polling & Fix Loop
- After opening a PR, monitor CI results. If CI fails or the PR is rejected, apply fixes on the same branch and re-push.
- A task is only "Done" when the PR is merged into `main`.

### 4. Conflict Resolution
- Attempt to resolve conflicts automatically. If the conflict is too complex, stop and ask for human intervention.

## Task Workflow

All tasks follow a strict lifecycle:

### Standard Task Workflow

1. **Select Task:** Choose the next available task from `plan.md`
2. **Mark In Progress:** Change the task from `[ ]` to `[~]`
3. **Write Failing Tests (Red):** Create tests that define expected behavior. Confirm they fail.
4. **Implement (Green):** Write minimum code to make tests pass. Confirm all pass.
5. **Refactor:** With passing tests, improve clarity and remove duplication. Rerun tests.
6. **Verify Coverage:** `pytest --cov=src --cov-report=html` → target >80% on new code.
7. **Document Deviations:** If implementation differs from tech stack: STOP, update `tech-stack.md`, then resume.
8. **Commit:** Stage all changes, commit with `<type>(<scope>): <description>` format.
9. **Attach Task Summary:** Use `git notes add -m "<summary>" <commit_hash>` to attach a detailed summary.
10. **Update Plan:** Mark task `[x]` in `plan.md` with first 7 chars of commit SHA.
11. **Commit Plan Update:** `conductor(plan): Mark task '<name>' as complete`

### Phase Completion Checklist

When a task completes a phase in `plan.md`:
1. Run `git diff --name-only <prev_checkpoint> HEAD` to identify changed files
2. Verify test files exist for all code changes; create missing tests
3. Run full test suite — max 2 fix attempts before asking for help
4. Propose manual verification steps to the user
5. Await user confirmation before proceeding
6. Create checkpoint commit: `conductor(checkpoint): End of Phase X`
7. Attach verification report via `git notes`
8. Update `plan.md` with checkpoint SHA: `[checkpoint: <sha>]`

### Quality Gates

Before marking any task complete:
- [ ] All tests pass
- [ ] Code coverage >80%
- [ ] Follows [code style guides](code_styleguides/)
- [ ] Public functions documented (docstrings/JSDoc)
- [ ] Type hints enforced
- [ ] No linting errors
- [ ] Documentation updated if needed

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

## Testing Requirements

### Unit Testing
- Every module must have corresponding tests
- Use fixtures for setup/teardown
- Mock external dependencies (ML models, file I/O)
- Test both success and failure cases

### Integration Testing
- Test complete user flows
- Test API endpoint responses
- Verify async task lifecycle

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
5. Implementation notes added to `plan.md`
6. Changes committed with proper message and git note attached

## Continuous Improvement

- Review workflow weekly
- Document lessons in `agent/LESSONS.md`
- Optimize for user happiness
- Keep things simple and maintainable
