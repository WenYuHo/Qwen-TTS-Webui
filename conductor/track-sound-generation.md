# Track: Sound Generation Performance & Quality

## Overview
- **Goal:** Systematically improve TTS voice generation quality, clarity, and performance across all voice types (preset, design, clone, mix).
- **Status:** ACTIVE
- **Owner:** Any Agent
- **Start Date:** 2026-03-05

---

## ⚠️ AGENT GUARDRAILS — READ FIRST

Every agent assigned to this track **MUST** follow these mandatory steps before writing code:

### Step 0: Memory Check (MANDATORY — DO THIS FIRST)
1. **Read** `agent/MEMORY.md` — understand current project state, folder structure, and core tenets
2. **Read** `agent/TASK_QUEUE.md` — check if your work overlaps with existing queue items
3. **Read** this track file — find the next `[ ]` task in the plan below
4. **Read** `conductor/index.md` — confirm you know the workflow and style sources

### Step 1: Understand the Rules
1. **Read** `conductor/workflow.md` — follow Standard Task Workflow phases (Red/Green/Refactor/Commit)
2. **Read** `conductor/code_styleguides/python.md` — Python conventions
3. **Read** `conductor/code_styleguides/javascript.md` — JS conventions  
4. **Read** `conductor/code_styleguides/html-css.md` — UI conventions (Technoid Brutalist)
5. **Read** `conductor/code_styleguides/agent-improvement.md` — Security, FastAPI routing, Pydantic V2

### Step 2: Verify Before Coding
- **Run tests first** to confirm a clean baseline: `python -m pytest tests/ -v --tb=short`
- **Check the environment**: read `.env` and `conductor/tech-stack.md` for dependencies

### Step 3: Work the Plan
- Pick the next `[ ]` task below, mark it `[~]`, follow TDD (Red→Green→Refactor), commit per `conductor/workflow.md`

---

## Phase 1: Voice Sample & Preview Quality 🎤

> **Why:** Generic preview text like "This is a preview of my voice" doesn't showcase a voice's range.
> Rich, phonetically-diverse sentences produce dramatically better audition results.

### Tasks

- [x] **1.1 — Curated Preview Text Pool**  
  Replace hardcoded preview text in `src/backend/api/voices.py` with a pool of 8+ phonetically-diverse sentences that rotate randomly.  
  **File:** `src/backend/api/voices.py`  
  **Acceptance:** Preview endpoint never returns the same boring generic sentence. Pool covers varied vowels, consonants, questions, exclamations, and emotional registers.

- [x] **1.2 — Custom Preview Text (Backend)**  
  Add `preview_text` optional field to `SpeakerProfile` schema. Update `/api/voice/preview` to use it when provided, falling back to the curated pool.  
  **Files:** `src/backend/api/schemas.py`, `src/backend/api/voices.py`  
  **Acceptance:** `POST /api/voice/preview` with `{"type":"preset","value":"aiden","preview_text":"Hello world!"}` speaks "Hello world!".

- [x] **1.3 — Custom Preview Text (Frontend)**  
  Add a "PREVIEW TEXT" input field in the Voice Studio section of `index.html`. Update `voicelab.js` and `shared.js` to send it with preview/segment requests.  
  **Files:** `src/static/index.html`, `src/static/voicelab.js`, `src/static/shared.js`  
  **Acceptance:** User types text in the input → any preview button uses that text. Empty → auto-curated text.

- [x] **1.4 — Rich Default Preview Sentences**  
  Replace hardcoded preview strings in `voicelab.js` for design/clone/mix previews with richer, more interesting sentences.  
  **File:** `src/static/voicelab.js`  
  **Acceptance:** Design preview says a weather/emotion sentence. Clone preview has dialogue. Mix preview tests knowledge range.

- [x] **1.5 — Clarity Instruct Hint**  
  Add `instruct="clear speech, natural delivery, steady pace"` to the preview endpoint for all voice types.  
  **File:** `src/backend/api/voices.py`  
  **Acceptance:** All previews sound clearer and more natural due to the instruct directive.

---

## Phase 2: Voice Cloning Quality (ICL Mode) 🧬

> **Why:** The model supports two cloning modes. `x_vector_only_mode=True` captures only timbre (speaker identity).
> ICL mode (`x_vector_only_mode=False` + `ref_text`) captures expressive similarity, prosody, and emotional nuances — significantly better quality.
> See: Qwen3-TTS docs — ICL mode produces "significantly improved voice similarity."

### Tasks

- [x] **2.1 — ref_text Schema Support**  
  Add `ref_text` optional field to `SpeakerProfile` in `schemas.py`.  
  **File:** `src/backend/api/schemas.py`  
  **Acceptance:** API accepts `ref_text` field without errors.

- [x] **2.2 — ICL Mode in PodcastEngine**  
  Update `PodcastEngine.generate_segment()` clone branch. When `profile["ref_text"]` is provided, use `x_vector_only_mode=False` with ICL. Fall back to current behavior when ref_text is absent.  
  **File:** `src/backend/podcast_engine.py`  
  **Key detail:** Use separate cache keys for ICL vs non-ICL prompts to avoid cache poisoning.  
  **Acceptance:** Clone with ref_text → ICL mode (more expressive). Clone without ref_text → x_vector_only (current behavior, no regression).

- [x] **2.3 — ref_text Frontend (Clone Tab)**  
  Add "Reference Transcript" textarea in the Voice Cloning card in `index.html`. Wire it in `voicelab.js` to send `ref_text` with clone requests.  
  **Files:** `src/static/index.html`, `src/static/voicelab.js`  
  **Acceptance:** User uploads audio + types transcript → ref_text is sent → ICL clone renders more nuanced speech.

- [x] **2.4 — ref_text in Preview Endpoint**  
  Update `/api/voice/preview` to pass `ref_text` through to `generate_segment`.  
  **File:** `src/backend/api/voices.py`  
  **Acceptance:** `POST /api/voice/preview` with `{"type":"clone","value":"path","ref_text":"Hello there"}` uses ICL mode.

---

## Phase 3: Advanced Generation Performance ⚡

> **Why:** Synthesis speed and memory efficiency directly affect UX responsiveness.
> The product's core tenet is "Stream-First Architecture" (from `agent/MEMORY.md`).

### Tasks

- [ ] **3.1 — Benchmark Baseline**

  **Goal:** Create a benchmark script that measures generation metrics for every voice type.

  **Create new file:** `tools/benchmark_tts.py`

  **Implementation steps:**
  1. Import `PodcastEngine` from `src.backend.podcast_engine` and `get_model` from `src.backend.model_loader`
  2. Define a standard 50-word test sentence
  3. For each voice type, measure the following:
     ```python
     import time, torch, numpy as np
     
     VOICE_TYPES = [
         {"name": "Preset",    "profile": {"type": "preset", "value": "Ryan"}},
         {"name": "Design",    "profile": {"type": "design", "value": "A calm male narrator with clear diction"}},
         {"name": "Clone",     "profile": {"type": "clone",  "value": "<path_to_test_audio>"}},
         {"name": "Clone+ICL", "profile": {"type": "clone",  "value": "<path_to_test_audio>", "ref_text": "Hello world test"}},
         {"name": "Mix",       "profile": {"type": "mix",    "value": json.dumps([{"profile": {"type":"preset","value":"Ryan"}, "weight": 0.5}, {"profile": {"type":"preset","value":"Serena"}, "weight": 0.5}])}},
     ]
     
     for vt in VOICE_TYPES:
         torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None
         start = time.perf_counter()
         wav, sr = engine.generate_segment(TEST_TEXT, profile=vt["profile"])
         elapsed = time.perf_counter() - start
         peak_vram = torch.cuda.max_memory_allocated() / 1e9 if torch.cuda.is_available() else 0
         duration = len(wav) / sr
         rtf = elapsed / duration  # Real-Time Factor (<1 = faster than real-time)
         print(f"{vt['name']:12s} | {elapsed:.2f}s | {duration:.2f}s audio | RTF {rtf:.2f} | {peak_vram:.2f}GB VRAM")
     ```
  4. Output results as a formatted table
  5. Save results to `tools/benchmark_results.json` for tracking over time

  **Acceptance:** `python tools/benchmark_tts.py` outputs a metrics table. RTF < 1.0 for preset voices.

---

- [ ] **3.2 — Prompt Caching Efficiency Audit**

  **Goal:** Ensure all cache pruning is consistent and no code path leaks memory.

  **File:** `src/backend/podcast_engine.py`

  **What to audit (with line references):**
  1. `generate_segment()` (line 210-271): Check clone branch (line 224-250) — already calls `prune_dict_cache(self.prompt_cache, limit=200, count=20)` ✅
  2. `generate_segment()` mix branch (line 251-262): Calls `prune_dict_cache` ✅
  3. `generate_podcast()` (line 349-516): Check clone branch at line 400-404 — **BUG:** Does NOT call `prune_dict_cache` before `self.prompt_cache[cache_key] = prompt` at line 413. Fix by adding prune call.
  4. `get_speaker_embedding()` (line 147-180): Check line 174 — calls prune ✅
  5. `_compute_mixed_embedding()` (line 273-289): Check line 278 — calls prune ✅

  **Fix required at line 411-413 of `podcast_engine.py`:**
  ```python
  # BEFORE (line 411):
                                  # ⚡ Bolt: Prevent unbounded growth of prompt cache
                                  prune_dict_cache(self.prompt_cache, limit=200, count=20)
  # This IS present, but verify it runs for BOTH clone and mix branches inside the loop
  ```

  **Also check:** `translation_cache` in `dub_audio()` (line 530) — calls prune ✅  
  **Also check:** `video_audio_cache` in `_extract_audio_with_cache()` (line 98) — calls prune ✅

  **Add cache hit rate logging:**
  ```python
  # Add to generate_segment() clone branch, after line 231:
  if icl_cache_key in self.prompt_cache:
      logger.debug(f"Cache HIT for clone prompt: {icl_cache_key[:20]}...")
      prompt = self.prompt_cache[icl_cache_key]
  else:
      logger.debug(f"Cache MISS for clone prompt: {icl_cache_key[:20]}...")
  ```

  **Acceptance:** All 8 cache dictionaries (`preset_embeddings`, `clone_embedding_cache`, `mix_embedding_cache`, `bgm_cache`, `prompt_cache`, `transcription_cache`, `translation_cache`, `video_audio_cache`) have prune calls before insertion. Document findings in commit note.

---

- [ ] **3.3 — Silence Padding for ICL (Anti-Bleed)**

  **Goal:** Prevent phoneme bleeding from the end of reference audio into generated speech.

  **File:** `src/backend/podcast_engine.py`

  **Where to modify:** `generate_segment()` clone branch (around line 241)

  **Implementation steps:**
  ```python
  # In generate_segment(), after resolving ref_audio (line 239-240), before calling create_voice_clone_prompt:
  
  ref_audio = str(resolved_paths[0])
  if VideoEngine.is_video(ref_audio): ref_audio = self._extract_audio_with_cache(ref_audio)
  
  # === ADD THIS: Silence padding for ICL anti-bleed ===
  if use_icl:
      import soundfile as sf
      audio_data, audio_sr = sf.read(ref_audio)
      # Append 0.5s silence to prevent phoneme bleed from ref into generated speech
      silence = np.zeros(int(audio_sr * 0.5), dtype=audio_data.dtype)
      padded = np.concatenate([audio_data, silence])
      # Write padded audio to a temp file (will be cleaned by StorageManager)
      padded_path = str(self.upload_dir / f"padded_{uuid.uuid4()}.wav")
      sf.write(padded_path, padded, audio_sr)
      ref_audio = padded_path
  # === END ADD ===
  
  prompt = model.create_voice_clone_prompt(
      ref_audio=ref_audio,
      ref_text=ref_text if use_icl else None,
      x_vector_only_mode=not use_icl
  )
  ```

  **Acceptance:** Clone+ICL speech starts cleanly — no bleed from the last phoneme of the reference audio.

---

- [ ] **3.4 — Reference Audio Quality Validation**

  **Goal:** Validate reference audio before expensive model operations.

  **File:** `src/backend/podcast_engine.py`

  **Where to add:** New method `_validate_ref_audio()`, called at the start of the clone branch in `generate_segment()` (before line 234).

  **Implementation:**
  ```python
  def _validate_ref_audio(self, audio_path: str) -> None:
      """Validate reference audio for cloning: duration, silence, format."""
      import soundfile as sf
      try:
          info = sf.info(audio_path)
          duration = info.duration
          if duration < 3.0:
              raise ValueError(f"Reference audio too short ({duration:.1f}s). Minimum 3 seconds required.")
          if duration > 30.0:
              raise ValueError(f"Reference audio too long ({duration:.1f}s). Maximum 30 seconds recommended for best quality.")
          
          # Check for silence-only input
          audio_data, sr = sf.read(audio_path)
          rms = np.sqrt(np.mean(audio_data ** 2))
          if rms < 0.001:  # Effectively silent
              raise ValueError("Reference audio appears to be silent. Please provide audio with speech.")
      except sf.SoundFileError as e:
          raise ValueError(f"Invalid audio file: {e}")
  ```

  **Call site** — add to `generate_segment()` clone branch, before line 241:
  ```python
  ref_audio = str(resolved_paths[0])
  if VideoEngine.is_video(ref_audio): ref_audio = self._extract_audio_with_cache(ref_audio)
  self._validate_ref_audio(ref_audio)  # <-- ADD THIS LINE
  ```

  **Acceptance:** Upload of <3s audio → error "Reference audio too short (2.1s). Minimum 3 seconds required." Upload of silent audio → error about silence.

---

- [ ] **3.5 — Generation Temperature Presets**

  **Goal:** Let users control generation randomness with friendly presets.

  **Qwen3 model kwargs (confirmed from `qwen3_tts_model.py` line 826-835):**
  ```python
  # These kwargs are forwarded to model.generate() via _merge_generate_kwargs():
  temperature: float = 0.9      # Higher = more random
  top_k: int = 50               # Top-K sampling
  top_p: float = 0.95           # Nucleus sampling
  repetition_penalty: float = 1.0
  ```

  **Step 1: Define presets in `src/backend/api/schemas.py`:**
  ```python
  # Add after line 50 (after StreamingSynthesisRequest):
  TEMPERATURE_PRESETS = {
      "consistent": {"temperature": 0.3, "top_k": 20, "top_p": 0.8, "repetition_penalty": 1.2},
      "balanced":   {"temperature": 0.9, "top_k": 50, "top_p": 0.95, "repetition_penalty": 1.0},
      "creative":   {"temperature": 1.2, "top_k": 80, "top_p": 0.98, "repetition_penalty": 0.9},
  }
  ```

  **Step 2: Add `temperature_preset` to `PodcastRequest` schema (line 27-35):**
  ```python
  class PodcastRequest(BaseModel):
      # ... existing fields ...
      temperature_preset: Optional[str] = "balanced"  # "consistent" | "balanced" | "creative"
  ```

  **Step 3: Pass kwargs in `generation.py` `run_synthesis_task()` (line 34-78):**
  ```python
  # After line 50, before calling generate_podcast or generate_segment:
  from .schemas import TEMPERATURE_PRESETS
  temp_kwargs = TEMPERATURE_PRESETS.get(request_data.temperature_preset or "balanced", TEMPERATURE_PRESETS["balanced"])
  ```
  Then pass `**temp_kwargs` to `generate_segment()` and `generate_podcast()`. This requires adding `**gen_kwargs` support to `PodcastEngine.generate_segment()`.

  **Step 4: Update `generate_segment()` signature** (line 210):
  ```python
  def generate_segment(self, text: str, profile: Dict[str, Any], language: str = "auto", 
                        model: Optional[Any] = None, instruct: Optional[str] = None,
                        **gen_kwargs) -> tuple[np.ndarray, int]:
  ```
  Then pass `**gen_kwargs` to each model call (lines 218, 223, 250, 262).

  **Step 5: Add UI dropdown in `src/static/index.html`** (in the settings/studio section):
  ```html
  <div class="control-group">
      <label class="label-industrial">GENERATION STYLE</label>
      <select id="temperature-preset">
          <option value="consistent">Consistent (steady, predictable)</option>
          <option value="balanced" selected>Balanced (default)</option>
          <option value="creative">Creative (varied, expressive)</option>
      </select>
  </div>
  ```

  **Step 6: Wire in `production.js`** — read `#temperature-preset` value and include in the `POST /api/generate/podcast` request body.

  **Acceptance:** Select "Consistent" → synthesis is more uniform. "Creative" → more expressive variation.

---

## Phase 4: Multi-Segment Clarity & Consistency 📊

> **Why:** Long-form content needs consistent voice quality across all segments.
> The product says "Efficient Batch Production" is a core goal.

### Tasks

- [ ] **4.1 — Per-Segment Quality Scoring**

  **Goal:** Compute quality metrics after each synthesis and log them.

  **File:** `src/backend/podcast_engine.py`

  **New method to add:**
  ```python
  @staticmethod
  def _compute_quality_score(wav: np.ndarray, sr: int) -> Dict[str, Any]:
      """Compute basic audio quality metrics for a generated segment."""
      duration = len(wav) / sr
      rms = float(np.sqrt(np.mean(wav ** 2)))
      peak = float(np.max(np.abs(wav)))
      # SNR estimate: ratio of signal RMS to noise floor (last 0.1s assumed silence)
      tail = wav[-int(sr * 0.1):] if len(wav) > int(sr * 0.1) else wav
      noise_rms = float(np.sqrt(np.mean(tail ** 2))) + 1e-10
      snr_db = 20 * np.log10(rms / noise_rms) if rms > 0 else 0
      clipping = bool(peak > 0.99)
      too_quiet = bool(rms < 0.01)
      return {
          "duration": round(duration, 2),
          "rms": round(rms, 4),
          "peak": round(peak, 4),
          "snr_db": round(snr_db, 1),
          "clipping": clipping,
          "too_quiet": too_quiet,
          "quality": "good" if (not clipping and not too_quiet and snr_db > 10) else "warning"
      }
  ```

  **Integration** — add to `generate_segment()` return path (before line 267):
  ```python
  quality = self._compute_quality_score(wavs[0], sr)
  logger.info(f"Segment quality: {quality}")
  audit_manager.log_event("synthesis", {"quality": quality, "profile_type": ptype}, quality["quality"])
  ```

  **Import needed:** `from .utils import audit_manager` (add to imports at top of file)

  **Acceptance:** Each segment logs quality metrics. Audit log shows `"quality": "good"` or `"quality": "warning"`.

---

- [ ] **4.2 — Auto-Retry on Low Quality**

  **Goal:** Automatically retry synthesis when output quality is poor.

  **File:** `src/backend/podcast_engine.py`

  **Where to modify:** `generate_segment()`, wrapping the return at line 267.

  **Implementation:**
  ```python
  # Replace the simple return at line 267 with:
  wav_out = self._apply_audio_watermark(wavs[0], sr)
  quality = self._compute_quality_score(wav_out, sr)
  
  # Auto-retry once with lower temperature if quality is bad
  if quality["quality"] == "warning" and not gen_kwargs.get("_is_retry"):
      logger.warning(f"Low quality detected (SNR={quality['snr_db']}dB), retrying with lower temperature")
      retry_kwargs = {**gen_kwargs, "temperature": 0.3, "top_k": 20, "_is_retry": True}
      return self.generate_segment(text, profile, language, model, instruct, **retry_kwargs)
  
  return wav_out, sr
  ```

  **Note:** The `_is_retry` flag prevents infinite retry loops.

  **Acceptance:** A garbled segment (clipping or near-silent) triggers one automatic retry. Retry uses more conservative parameters.

---

- [ ] **4.3 — Cross-Segment Consistency Check**

  **Goal:** Detect voice drift in long-form podcast generation.

  **File:** `src/backend/podcast_engine.py`

  **Where to add:** `generate_podcast()`, after all segments are generated (after line 428, before mixing at line 430).

  **Implementation:**
  ```python
  # After all waveforms are generated, before mixing:
  # Check speaker embedding consistency across segments
  speaker_first_emb = {}  # role -> embedding of first segment
  for i, item in enumerate(script):
      if waveforms[i] is None: continue
      role = item.get("role")
      profile = profiles.get(role)
      if profile is None: continue
      try:
          emb = self.get_speaker_embedding(profile)
          if emb is not None:
              if role not in speaker_first_emb:
                  speaker_first_emb[role] = emb
              else:
                  # Cosine similarity
                  cos_sim = float(torch.nn.functional.cosine_similarity(
                      speaker_first_emb[role].unsqueeze(0), emb.unsqueeze(0)
                  ))
                  if cos_sim < 0.85:  # 15% drift threshold
                      logger.warning(f"Voice drift detected for speaker '{role}' at segment {i}: "
                                     f"similarity={cos_sim:.2f} (threshold=0.85)")
      except Exception:
          pass  # Don't block generation for embedding comparison failures
  ```

  **Acceptance:** Log warns if segment #N has >15% embedding distance from segment #1 for same speaker.

---

- [ ] **4.4 — Post-Processing Pipeline Enhancement**

  **Goal:** Add broadcast-quality audio processing to `AudioPostProcessor`.

  **File:** `src/backend/utils.py` (class `AudioPostProcessor`, starts at line 119)

  **Add these new methods to the class:**

  ```python
  @staticmethod
  def apply_compression(wav: np.ndarray, threshold_db: float = -20.0, ratio: float = 4.0) -> np.ndarray:
      """Gentle dynamic range compression for broadcast consistency."""
      try:
          threshold = 10 ** (threshold_db / 20.0)
          out = wav.copy()
          mask = np.abs(out) > threshold
          out[mask] = np.sign(out[mask]) * (threshold + (np.abs(out[mask]) - threshold) / ratio)
          return out
      except Exception:
          return wav

  @staticmethod
  def apply_deesser(wav: np.ndarray, sr: int, freq: float = 6000.0, reduction_db: float = -6.0) -> np.ndarray:
      """Reduce sibilance (s, sh, ch sounds) in the 4-8kHz range."""
      if scipy_signal is None:
          return wav
      try:
          # Isolate sibilant frequencies
          b, a = scipy_signal.butter(2, [4000 / (sr/2), 8000 / (sr/2)], btype='bandpass')
          sibilant = scipy_signal.lfilter(b, a, wav)
          # Reduce sibilant energy
          reduction = 10 ** (reduction_db / 20.0)
          return wav - sibilant * (1.0 - reduction)
      except Exception:
          return wav
  ```

  **Integration** — add toggle in `SystemSettings` in `src/backend/api/system.py` (line 17-19):
  ```python
  class SystemSettings(BaseModel):
      watermark_audio: bool = True
      watermark_video: bool = True
      post_processing: bool = False  # <-- ADD: enables compression + de-essing
  ```

  **Apply in `generate_podcast()`** at line 506-507, after EQ and reverb:
  ```python
  final_wav = AudioPostProcessor.apply_eq(final_wav, sample_rate, preset=eq_preset)
  final_wav = AudioPostProcessor.apply_reverb(final_wav, sample_rate, intensity=reverb_level)
  
  # Post-processing: gentle compression + de-essing
  if getattr(_settings, 'post_processing', False):
      final_wav = AudioPostProcessor.apply_compression(final_wav)
      final_wav = AudioPostProcessor.apply_deesser(final_wav, sample_rate)
  ```

  **Import `_settings`:** Already imported at line 184 via `from .api.system import _settings`.

  **Acceptance:** Toggle "Post Processing" in settings. When enabled, output has consistent RMS and reduced sibilance.

---

## Phase 5: Testing & Verification ✅

> **Why:** Every phase needs tests per `conductor/workflow.md` TDD requirement.

### Tasks

- [ ] **5.1 — Unit Tests for Preview Text Pool**

  **New file:** `tests/test_voice_preview.py`

  ```python
  import pytest
  from unittest.mock import patch, MagicMock
  from src.backend.api.voices import PREVIEW_TEXTS
  
  def test_preview_pool_has_diverse_sentences():
      assert len(PREVIEW_TEXTS) >= 8, "Pool should have at least 8 sentences"
      # Check variety: questions, exclamations, quotes
      has_question = any("?" in t for t in PREVIEW_TEXTS)
      has_exclamation = any("!" in t for t in PREVIEW_TEXTS)
      has_quote = any("'" in t or '"' in t for t in PREVIEW_TEXTS)
      assert has_question and has_exclamation and has_quote
  
  @pytest.mark.asyncio
  async def test_preview_uses_custom_text():
      """POST /api/voice/preview with preview_text should use that text."""
      from httpx import AsyncClient, ASGITransport
      from src.backend.server import app
      async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
          with patch("src.backend.server_state.engine") as mock_engine:
              mock_engine.generate_segment.return_value = (np.zeros(24000), 24000)
              resp = await client.post("/api/voice/preview", json={
                  "type": "preset", "value": "ryan", "preview_text": "Custom test text"
              })
      # Verify generate_segment was called with "Custom test text"
      mock_engine.generate_segment.assert_called_once()
      call_args = mock_engine.generate_segment.call_args
      assert call_args.kwargs.get("text") == "Custom test text" or call_args[0][0] == "Custom test text"
  ```

---

- [ ] **5.2 — Unit Tests for ICL Mode Toggle**

  **New file:** `tests/test_clone_icl.py`

  ```python
  import pytest
  from unittest.mock import patch, MagicMock
  from src.backend.podcast_engine import PodcastEngine
  
  @pytest.fixture
  def engine():
      with patch("src.backend.podcast_engine.get_model"):
          e = PodcastEngine()
          return e
  
  def test_clone_without_ref_text_uses_xvector_only(engine):
      """Clone without ref_text should set x_vector_only_mode=True."""
      with patch.object(engine, '_resolve_paths', return_value=['/fake/audio.wav']):
          mock_model = MagicMock()
          mock_model.create_voice_clone_prompt.return_value = [MagicMock()]
          mock_model.generate_voice_clone.return_value = ([np.zeros(24000)], 24000)
          
          engine.generate_segment("Hello", {"type": "clone", "value": "test.wav"}, model=mock_model)
          
          mock_model.create_voice_clone_prompt.assert_called_once()
          call_kwargs = mock_model.create_voice_clone_prompt.call_args
          assert call_kwargs.kwargs.get("x_vector_only_mode") == True
  
  def test_clone_with_ref_text_uses_icl(engine):
      """Clone with ref_text should set x_vector_only_mode=False (ICL mode)."""
      with patch.object(engine, '_resolve_paths', return_value=['/fake/audio.wav']):
          mock_model = MagicMock()
          mock_model.create_voice_clone_prompt.return_value = [MagicMock()]
          mock_model.generate_voice_clone.return_value = ([np.zeros(24000)], 24000)
          
          engine.generate_segment("Hello", {"type": "clone", "value": "test.wav", "ref_text": "Test transcript"}, model=mock_model)
          
          call_kwargs = mock_model.create_voice_clone_prompt.call_args
          assert call_kwargs.kwargs.get("x_vector_only_mode") == False
          assert call_kwargs.kwargs.get("ref_text") == "Test transcript"
  ```

---

- [ ] **5.3 — Integration Test: Full Clone Workflow**

  Expand `tests/test_voicelab_integration.py` with a test that uploads audio → provides ref_text → generates clone preview → verifies valid WAV output.

---

- [ ] **5.4 — Update Existing Tests**

  Update `tests/test_api.py` to test the `preview_text` field in `SpeakerProfile`.  
  Update `tests/test_engine.py` to test `generate_segment()` with `ref_text`.  
  Update schema tests for new `temperature_preset` field on `PodcastRequest`.

---

## Key Files Reference

| File | Purpose | Key Lines |
|------|---------|-----------|
| `src/backend/api/voices.py` | Preview endpoint, PREVIEW_TEXTS pool | L17-26 (texts), L77-101 (preview endpoint) |
| `src/backend/api/schemas.py` | SpeakerProfile, PodcastRequest, all schemas | L4-9 (SpeakerProfile), L27-35 (PodcastRequest) |
| `src/backend/api/generation.py` | Synthesis endpoints, `run_synthesis_task` | L34-78 (task runner), L101-146 (endpoints) |
| `src/backend/podcast_engine.py` | Core engine: generate_segment, generate_podcast | L210-271 (generate_segment), L349-516 (podcast) |
| `src/backend/qwen_tts/inference/qwen3_tts_model.py` | Model API | L390-515 (create_clone_prompt), L526-692 (generate_clone), L792-902 (custom_voice) |
| `src/backend/utils.py` | AudioPostProcessor, AuditManager, prune_dict_cache | L31-44 (prune), L119-232 (AudioPostProcessor) |
| `src/static/index.html` | UI layout | Temperature preset dropdown, settings area |
| `src/static/voicelab.js` | Voice lab JS | L6-69 (design), L71-140 (clone), L142-206 (mix) |
| `src/static/production.js` | Production JS | L5-132 (generatePodcast) |

---

## Qwen3 Model API Quick Reference

```python
# CustomVoice (preset voices with instruct):
model.generate_custom_voice(text, speaker, language, instruct, temperature=0.9, top_k=50, top_p=0.95)

# VoiceDesign (describe-a-voice with instruct):
model.generate_voice_design(text, instruct, language, temperature=0.9, top_k=50, top_p=0.95)

# Base - Clone Prompt (creates reusable prompt):
prompt = model.create_voice_clone_prompt(ref_audio, ref_text=None, x_vector_only_mode=False)
# Returns: List[VoiceClonePromptItem] with fields: ref_code, ref_spk_embedding, x_vector_only_mode, icl_mode, ref_text

# Base - Voice Clone (generates speech from prompt):
model.generate_voice_clone(text, language, voice_clone_prompt=prompt, instruct=None, temperature=0.9, top_k=50, top_p=0.95)
```

---

## Recent Updates

### 2026-03-05: Bootstrap — Phases 1 & 2 Implemented
- Created track. Phases 1 & 2 tasks implemented (curated preview text, custom preview text, ICL cloning mode, ref_text support).
- Phase 3–5 planned with detailed implementation guides, code snippets, and exact line references.
- Code changes in: `voices.py`, `schemas.py`, `podcast_engine.py`, `index.html`, `voicelab.js`, `shared.js`.

