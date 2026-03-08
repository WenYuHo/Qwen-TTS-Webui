# Testing Library Audit Report

## Current State Analysis

The project currently uses a fragmented testing stack with several redundancies and inconsistencies.

### 1. Framework Inconsistency
- **Primary Runner**: `pytest` is the main entry point (as seen in `requirements.txt` and `package.json`).
- **Legacy Components**: 5 major test files still use `unittest.TestCase` (`test_config.py`, `test_task_manager.py`, etc.).
- **Redundant Imports**: Files like `test_synthesis_errors.py` import both `pytest` and `unittest` but only use one, or import `pytest` without using any of its features.

### 2. Client Inconsistency
- **Sync Client**: `fastapi.testclient.TestClient` is used in ~90% of API tests.
- **Async Client**: `httpx.AsyncClient` is used in `test_voice_preview.py`.
- **Impact**: Inconsistent testing of async behavior and potential issues with background tasks (which `TestClient` handles synchronously by default).

### 3. Structural Redundancy
- **Root-level Scripts**: Files like `test_sox.py`, `test_pydub.py`, and `test_generation.py` exist in the root directory. These are manual validation scripts rather than integrated unit/integration tests.
- **Path Management**: Almost every test file manually manipulates `sys.path`.

### 4. UI Test Fragility
- **Server Lifecycle**: `test_voicelab_ui.py` manually spawns a subprocess for the server. This is prone to "port already in use" errors and orphaned processes if the test runner crashes.

## Recommended Consolidation Plan

1. **Standardize on Pytest Native**:
    - Refactor `unittest.TestCase` classes into plain functions with `assert` statements.
    - Standardize on `pytest` fixtures for setup/teardown.

2. **Unified API Testing**:
    - Migrate all `TestClient` usage to `httpx.AsyncClient` to better simulate production async flows.

3. **Centralized Infrastructure**:
    - Move all root-level `test_*.py` scripts into `tests/internal/` or `tests/utils/` and convert them to formal pytest suites.
    - Consolidate `sys.path` logic into `tests/conftest.py`.

4. **Robust E2E setup**:
    - Use a more robust server fixture (possibly using `uvicorn.Server` in a thread or process managed strictly by pytest).

---
*Decision Logged: 2026-03-08*
*Action: Proposed refactor of testing infrastructure.*
