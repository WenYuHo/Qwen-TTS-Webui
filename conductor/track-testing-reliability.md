# Track: Testing & Reliability

## Overview
- **Goal:** Achieve comprehensive test coverage (>80%) across all modules, establish E2E browser testing, and build a CI-safe test suite that catches regressions before they hit production.
- **Status:** PLANNED
- **Owner:** Any Agent
- **Start Date:** TBD

---

## ⚠️ AGENT GUARDRAILS — READ FIRST

### Step 0: Memory Check (MANDATORY)
1. **Read** `agent/MEMORY.md` — understand project state and active tracks
2. **Read** `agent/TASK_QUEUE.md` — check for overlapping work
3. **Read** this track file — find the next `[ ]` task
4. **Read** `conductor/workflow.md` — TDD requirements and testing standards

### Step 1: Understand Current Coverage
- Run `python -m pytest tests/ -v --tb=short` for full suite status
- Run `python -m pytest --co -q tests/` to list all test names
- Run `python -m pytest --cov=src --cov-report=html tests/` for coverage report

---

## Phase 1: Coverage Gap Analysis & Quick Wins 🔍

> **Why:** 33 test files exist but coverage is unknown. Some modules likely have 0% coverage.

### Current `conftest.py` (16 lines — only adds `src/` to path + mocks sox):
```python
# tests/conftest.py (as of now):
import sys, os
from pathlib import Path
src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path not in sys.path: sys.path.insert(0, src_path)
try: import backend.sox_shim as sox_shim; sox_shim.mock_sox()
except: pass
```

### Tasks

- [ ] **1.1 — Generate Coverage Baseline**

  **Step 1: Run coverage and save:**
  ```bash
  python -m pytest --cov=src --cov-report=term-missing --cov-report=html:tests/htmlcov tests/
  ```

  **Step 2: Create `tests/coverage_baseline.md` from output:**
  ```markdown
  # Coverage Baseline — [DATE]
  
  | Module | Lines | Covered | Missing | Coverage |
  |--------|-------|---------|---------|----------|
  | podcast_engine.py | 537 | ??? | ??? | ??% |
  | api/generation.py | 163 | ??? | ??? | ??% |
  | api/voices.py | 124 | ??? | ??? | ??% |
  | api/video.py | 297 | ??? | ??? | ??% |
  | utils.py | 433 | ??? | ??? | ??% |
  | ... | | | | |
  
  **Target:** >80% on all core modules.
  **Priority gaps:** Modules below 50%.
  ```

  **Acceptance:** Markdown file listing every module with coverage %. Modules <80% flagged.

---

- [ ] **1.2 — Fix Broken/Skipped Tests**

  **Step 1: Run full suite and identify failures:**
  ```bash
  python -m pytest tests/ -v --tb=short 2>&1 | tee tests/test_results.txt
  ```

  **Step 2: Common fix patterns:**
  ```python
  # Pattern 1: Missing import after refactor
  # If test imports `from backend.engine import Engine` but it moved:
  from backend.podcast_engine import PodcastEngine  # Fix import path
  
  # Pattern 2: Test depends on hardware (GPU, mic, model file)
  @pytest.mark.skipif(not torch.cuda.is_available(), reason="No GPU")
  def test_gpu_synthesis(): ...
  
  # Pattern 3: Flaky async test (missing await)
  @pytest.mark.asyncio
  async def test_api_endpoint():
      async with httpx.AsyncClient(app=app, base_url="http://test") as client:
          response = await client.get("/api/system/status")
  ```

  **Acceptance:** `pytest tests/ -v` → 100% pass, 0 errors.

---

- [ ] **1.3 — Test Fixtures & Conftest Upgrade**

  **Rewrite `tests/conftest.py` with reusable fixtures:**
  ```python
  import sys
  import os
  import pytest
  import numpy as np
  from pathlib import Path
  from unittest.mock import MagicMock, patch
  
  # Add src to PYTHONPATH
  src_path = str(Path(__file__).resolve().parent.parent / "src")
  if src_path not in sys.path:
      sys.path.insert(0, src_path)
  
  # Mock sox before anything else
  try:
      import backend.sox_shim as sox_shim
      sox_shim.mock_sox()
  except Exception:
      pass
  
  
  @pytest.fixture
  def mock_model():
      """Mock Qwen3-TTS model that returns deterministic audio."""
      model = MagicMock()
      # generate_custom_voice returns (waveform_list, sample_rate)
      model.generate_custom_voice.return_value = (
          [np.random.randn(24000).astype(np.float32)], 24000
      )
      model.generate_voice_design.return_value = (
          [np.random.randn(24000).astype(np.float32)], 24000
      )
      model.generate_voice_clone.return_value = (
          [np.random.randn(24000).astype(np.float32)], 24000
      )
      model.get_supported_languages.return_value = ["zh","en","ja","ko","de","fr","ru","pt","es","it"]
      model.create_voice_clone_prompt.return_value = [MagicMock(
          ref_code=np.zeros((1, 256)),
          ref_spk_embedding=np.zeros(256)
      )]
      return model
  
  
  @pytest.fixture
  def mock_engine(mock_model):
      """Mock PodcastEngine with mocked model."""
      with patch("backend.podcast_engine.get_model", return_value=mock_model):
          from backend.podcast_engine import PodcastEngine
          engine = PodcastEngine()
          yield engine
  
  
  @pytest.fixture
  def test_audio():
      """Generate a 3-second test audio at 24kHz."""
      sr = 24000
      duration = 3.0
      t = np.linspace(0, duration, int(sr * duration), endpoint=False)
      # 440 Hz sine wave
      wav = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
      return wav, sr
  
  
  @pytest.fixture
  def test_audio_file(test_audio, tmp_path):
      """Save test audio to a temp WAV file."""
      import soundfile as sf
      wav, sr = test_audio
      path = tmp_path / "test_input.wav"
      sf.write(str(path), wav, sr)
      return str(path)
  
  
  @pytest.fixture
  def sample_profiles():
      """Sample voice profiles for testing."""
      return {
          "Alice": {"type": "preset", "value": "Aiden"},
          "Bob": {"type": "design", "value": "A deep male voice with warm tones"},
      }
  
  
  @pytest.fixture
  def sample_script():
      """Sample podcast script for testing."""
      return [
          {"role": "Alice", "text": "Hello and welcome to the show.", "language": "en"},
          {"role": "Bob", "text": "Thanks for having me.", "language": "en"},
          {"role": "Alice", "text": "Let's get started.", "language": "en"},
      ]
  
  
  @pytest.fixture
  def app_client():
      """Async test client for FastAPI app."""
      import httpx
      from backend.main import app
      return httpx.AsyncClient(app=app, base_url="http://test")
  ```

  **Acceptance:** Tests can write `def test_x(mock_engine, test_audio): ...` and get clean fixtures.

---

## Phase 2: Module-Level Unit Tests ✅

> **Why:** Core business logic in `podcast_engine.py` and API endpoints need thorough unit testing.

### Tasks

- [ ] **2.1 — PodcastEngine Unit Tests**

  **File:** `tests/test_engine.py`

  **Test function templates:**
  ```python
  def test_generate_segment_preset(mock_engine, mock_model):
      """Test preset voice synthesis."""
      wav, sr = mock_engine.generate_segment(
          text="Hello world",
          profile={"type": "preset", "value": "Aiden"},
          language="en"
      )
      assert isinstance(wav, np.ndarray)
      assert sr == 24000
      assert len(wav) > 0
      mock_model.generate_custom_voice.assert_called_once()
  
  def test_generate_segment_design(mock_engine, mock_model):
      """Test design voice synthesis."""
      wav, sr = mock_engine.generate_segment(
          text="Hello world",
          profile={"type": "design", "value": "A deep voice"},
          language="en"
      )
      mock_model.generate_voice_design.assert_called_once()
  
  def test_generate_segment_clone_icl(mock_engine, mock_model, test_audio_file):
      """Test clone with ICL mode (ref_text provided)."""
      wav, sr = mock_engine.generate_segment(
          text="Hello world",
          profile={"type": "clone", "value": test_audio_file, "ref_text": "Original text"},
          language="en"
      )
      # Should use x_vector_only_mode=False for ICL
      mock_model.create_voice_clone_prompt.assert_called_once()
      call_args = mock_model.create_voice_clone_prompt.call_args
      assert call_args.kwargs.get("x_vector_only_mode") == False
  
  def test_generate_segment_empty_text(mock_engine):
      """Test that empty text raises or returns gracefully."""
      with pytest.raises(Exception):
          mock_engine.generate_segment(text="", profile={"type": "preset", "value": "Aiden"})
  
  def test_generate_podcast(mock_engine, sample_script, sample_profiles):
      """Test full podcast generation."""
      result = mock_engine.generate_podcast(sample_script, sample_profiles)
      assert result is not None
      assert "waveform" in result or isinstance(result, dict)
  ```

  **Coverage target:** >85% on `podcast_engine.py`.

---

- [ ] **2.2 — API Endpoint Tests**

  **File:** `tests/test_api.py`

  ```python
  import pytest
  import httpx
  
  @pytest.mark.asyncio
  async def test_system_status(app_client):
      async with app_client as client:
          response = await client.get("/api/system/status")
          assert response.status_code == 200
          data = response.json()
          assert "status" in data
  
  @pytest.mark.asyncio
  async def test_voice_speakers(app_client):
      async with app_client as client:
          response = await client.get("/api/voice/speakers")
          assert response.status_code == 200
          data = response.json()
          assert "presets" in data
          assert len(data["presets"]) > 0
  
  @pytest.mark.asyncio
  async def test_voice_library_crud(app_client):
      async with app_client as client:
          # GET library
          response = await client.get("/api/voice/library")
          assert response.status_code == 200
          # POST to save
          lib = response.json()
          response = await client.post("/api/voice/library",
              json={"voices": lib.get("voices", [])})
          assert response.status_code == 200
  
  @pytest.mark.asyncio
  async def test_generate_segment_endpoint(app_client):
      async with app_client as client:
          response = await client.post("/api/generate/segment", json={
              "profiles": [{"role": "test", "type": "preset", "value": "Aiden"}],
              "script": [{"role": "test", "text": "Hello world"}]
          })
          assert response.status_code == 200
          data = response.json()
          assert "task_id" in data
  ```

  **Acceptance:** Every `@router` endpoint has a test with correct status codes.

---

- [ ] **2.3 — Schema Validation Tests**

  **File:** `tests/test_schemas.py`

  ```python
  import pytest
  from pydantic import ValidationError
  from backend.api.schemas import SpeakerProfile, PodcastRequest, NarratedVideoRequest
  
  def test_speaker_profile_valid():
      p = SpeakerProfile(type="preset", value="Aiden")
      assert p.type == "preset"
  
  def test_speaker_profile_with_ref_text():
      p = SpeakerProfile(type="clone", value="file.wav", ref_text="Hello")
      assert p.ref_text == "Hello"
  
  def test_speaker_profile_missing_type():
      with pytest.raises(ValidationError):
          SpeakerProfile(value="Aiden")  # Missing required 'type'
  
  def test_podcast_request_defaults():
      r = PodcastRequest(profiles={}, script=[])
      assert r.eq_preset == "flat"
      assert r.bgm_mood is None
  
  def test_narrated_video_request_backward_compat():
      r = NarratedVideoRequest(prompt="test", narration_text="hello")
      assert r.width == 768
  ```

  **Acceptance:** All schema models tested for valid/invalid inputs.

---

- [ ] **2.4 — Utility Tests**

  **File:** `tests/test_system_utils.py`

  ```python
  from backend.utils import AudioPostProcessor, numpy_to_wav_bytes
  import numpy as np
  
  def test_numpy_to_wav_bytes():
      wav = np.random.randn(24000).astype(np.float32)
      result = numpy_to_wav_bytes(wav, 24000)
      assert isinstance(result, bytes)
      assert len(result) > 0
      # Should start with RIFF header
      assert result[:4] == b'RIFF'
  
  def test_audio_post_processor_eq():
      pp = AudioPostProcessor()
      wav = np.random.randn(24000).astype(np.float32)
      result = pp.apply_eq(wav, 24000, preset="warm")
      assert len(result) == len(wav)
  
  def test_audio_post_processor_normalize():
      pp = AudioPostProcessor()
      wav = np.random.randn(24000).astype(np.float32) * 0.1  # Quiet signal
      result = pp.normalize(wav)
      assert np.max(np.abs(result)) > np.max(np.abs(wav))  # Louder after normalization
  ```

---

- [ ] **2.5 — Security Tests**

  **File:** `tests/test_security.py`

  ```python
  import pytest
  
  def test_path_traversal_basic(mock_engine):
      with pytest.raises(Exception):
          mock_engine._resolve_paths("../../etc/passwd")
  
  def test_path_traversal_encoded(mock_engine):
      with pytest.raises(Exception):
          mock_engine._resolve_paths("..%2F..%2Fetc%2Fpasswd")
  
  def test_path_traversal_absolute(mock_engine):
      with pytest.raises(Exception):
          mock_engine._resolve_paths("/etc/passwd")
  
  def test_path_traversal_null_byte(mock_engine):
      with pytest.raises(Exception):
          mock_engine._resolve_paths("valid_file.wav\x00.txt")
  
  def test_valid_path_resolves(mock_engine, test_audio_file):
      # Valid path should resolve without error
      result = mock_engine._resolve_paths(test_audio_file)
      assert len(result) > 0
  ```

  **Acceptance:** All malicious inputs rejected. Valid inputs pass.

---

## Phase 3: Integration & E2E Tests 🔗

> **Why:** Unit tests catch component bugs but miss integration issues.

### Tasks

- [ ] **3.1 — Full Podcast Generation E2E**

  **File:** `tests/test_e2e_synthesis.py`

  ```python
  @pytest.mark.integration
  def test_podcast_e2e(mock_engine, sample_script, sample_profiles):
      """Full pipeline: parse script → generate all segments → merge → valid output."""
      result = mock_engine.generate_podcast(
          script=sample_script,
          profiles=sample_profiles,
          bgm_mood=None, eq_preset="flat"
      )
      assert result is not None
      wav = result.get("waveform") or result.get("combined_wav")
      assert wav is not None
      assert len(wav) > 24000  # At least 1 second of audio
  ```

  **Run with:** `pytest tests/test_e2e_synthesis.py -m integration -v`

---

- [x] **3.2 — Voice Clone E2E**

  ```python
  @pytest.mark.integration
  def test_voice_clone_e2e(mock_engine, test_audio_file):
      wav, sr = mock_engine.generate_segment(
          text="This is a cloned voice test.",
          profile={"type": "clone", "value": test_audio_file}
      )
      assert sr == 24000
      assert len(wav) > 0
  ```

---

- [x] **3.3 — Browser Smoke Test**

  **File:** `tests/test_browser_smoke.py` — requires Playwright:
  ```python
  import pytest
  
  @pytest.mark.browser
  def test_homepage_loads(start_server):
      """Verify all tabs render without JS errors."""
      # ... (implemented)
  ```

  **Run with:** `pytest tests/test_browser_smoke.py -m browser -v`

---

- [ ] **3.4 — API Load Test**

  **File:** `tests/test_load.py`:
  ```python
  import asyncio
  import httpx
  import pytest
  
  @pytest.mark.asyncio
  @pytest.mark.load
  async def test_concurrent_previews():
      """10 concurrent preview requests shouldn't crash the server."""
      async with httpx.AsyncClient(base_url="http://localhost:7860") as client:
          tasks = [
              client.post("/api/voice/preview", json={"type": "preset", "value": "Aiden"})
              for _ in range(10)
          ]
          results = await asyncio.gather(*tasks, return_exceptions=True)
          successes = [r for r in results if isinstance(r, httpx.Response) and r.status_code == 200]
          assert len(successes) >= 8  # Allow 2 failures under load
  ```

---

## Phase 4: CI/CD & Automation 🤖

> **Why:** Tests are only useful if they run automatically.

### Tasks

- [ ] **4.1 — GitHub Actions Workflow**

  **File:** `.github/workflows/test.yml`:
  ```yaml
  name: Tests
  on: [push, pull_request]
  
  jobs:
    test:
      runs-on: ubuntu-latest
      strategy:
        matrix:
          python-version: ["3.9", "3.10", "3.11"]
      
      steps:
        - uses: actions/checkout@v4
        - name: Set up Python ${{ matrix.python-version }}
          uses: actions/setup-python@v5
          with:
            python-version: ${{ matrix.python-version }}
        
        - name: Install dependencies
          run: |
            pip install -r requirements.txt
            pip install pytest pytest-cov pytest-asyncio httpx
        
        - name: Run tests
          run: |
            python -m pytest tests/ -v --tb=short \
              --cov=src --cov-report=xml \
              -m "not browser and not load and not integration"
        
        - name: Upload coverage
          uses: codecov/codecov-action@v4
          with:
            file: ./coverage.xml
  ```

  **Acceptance:** Push → tests run → green/red badge.

---

- [ ] **4.2 — Pre-Commit Hooks**

  **File:** `.pre-commit-config.yaml`:
  ```yaml
  repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.3.0
      hooks:
        - id: ruff
          args: [--fix]
    
    - repo: https://github.com/psf/black
      rev: 24.2.0
      hooks:
        - id: black
    
    - repo: local
      hooks:
        - id: fast-tests
          name: Fast Unit Tests
          entry: python -m pytest tests/ -x -q -m "not browser and not load and not integration"
          language: system
          pass_filenames: false
          always_run: true
  ```

  **Setup:** `pip install pre-commit && pre-commit install`

---

- [ ] **4.3 — Test Data Fixtures**

  **Create `tests/fixtures/` directory structure:**
  ```
  tests/fixtures/
  ├── audio_3s_440hz.wav       # 3-second 440Hz sine at 24kHz
  ├── audio_10s_speech.wav     # 10-second speech sample
  ├── audio_silence.wav        # 3-second silence (for edge cases)
  ├── sample_script.json       # {"script": [...], "profiles": {...}}
  └── sample_project.json      # Full project JSON for load testing
  ```

  **Generate fixture files in conftest.py:**
  ```python
  @pytest.fixture(scope="session")
  def fixtures_dir():
      return Path(__file__).parent / "fixtures"
  
  @pytest.fixture(scope="session", autouse=True)
  def generate_fixtures(fixtures_dir):
      """Auto-generate audio fixtures if they don't exist."""
      fixtures_dir.mkdir(exist_ok=True)
      import soundfile as sf
      
      # 3s sine wave
      path = fixtures_dir / "audio_3s_440hz.wav"
      if not path.exists():
          t = np.linspace(0, 3, 72000, endpoint=False)
          wav = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
          sf.write(str(path), wav, 24000)
      
      # 3s silence
      path = fixtures_dir / "audio_silence.wav"
      if not path.exists():
          sf.write(str(path), np.zeros(72000, dtype=np.float32), 24000)
  ```

  **Acceptance:** Tests use fixtures instead of generating audio on-the-fly.

---

## Key Files Reference

| File | Purpose | Key Lines |
|------|---------|-----------|
| `tests/conftest.py` | Fixtures: `mock_engine`, `mock_model`, `test_audio`, `sample_script` | L1-16 (current), upgrade to ~100 lines |
| `tests/test_engine.py` | PodcastEngine unit tests | All generate_ methods |
| `tests/test_api.py` | API endpoint tests with httpx | All @router endpoints |
| `tests/test_schemas.py` | [NEW] Pydantic validation tests | SpeakerProfile, PodcastRequest |
| `tests/test_security.py` | Path traversal tests | `_resolve_paths()` edge cases |
| `tests/test_e2e_synthesis.py` | E2E pipeline tests | Full podcast generation |
| `tests/test_browser_smoke.py` | [NEW] Playwright browser tests | UI tab loading |
| `.github/workflows/test.yml` | [NEW] CI/CD pipeline | pytest matrix |

