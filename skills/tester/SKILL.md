---
name: tester
description: Standardizes the TDD workflow, browser automation, and audio quality auditing for the project. Use when adding new features, fixing bugs, or increasing test coverage.
---

# Tester Skill

This skill enforces the **Strict TDD** mandate of the project.

## 🧪 Testing Protocol

### 1. Test-First Implementation
- **CREATE** the test file in `tests/` BEFORE modifying any source code.
- **RUN** `pytest` and confirm it fails.
- **IMPLEMENT** the minimal code required to make the test pass.
- **REFACTOR** for performance or readability without breaking the test.

### 2. Audio Validation
For audio engine tests:
- Use `tests/audio_quality_audit.py` for automated SNR or bit-depth checks.
- Mock external synthesis APIs unless explicitly performing E2E testing.

### 3. Browser Automation (Playwright)
For UI tests:
- Reference `tests/test_e2e_ui_flow.py`.
- Ensure `src/server.py` is running in a background task or mock the API responses.

## 📋 Target Directories
- `tests/` (Unit & Integration)
- `tests/internal/` (Core Engine Tests)
- `tests/audio_quality_audit.py`
