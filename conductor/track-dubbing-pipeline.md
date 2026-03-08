# Track: Dubbing & Voice Conversion Pipeline

## Overview
- **Goal:** Transform the basic dubbing and S2S (Speech-to-Speech) features into a production-ready pipeline with progress tracking, language detection, prosody preservation, and multi-speaker dubbing.
- **Status:** PLANNED
- **Owner:** Any Agent
- **Start Date:** TBD

---

## ⚠️ AGENT GUARDRAILS — READ FIRST

### Step 0: Memory Check (MANDATORY)
1. **Read** `agent/MEMORY.md` — understand project state and active tracks
2. **Read** `agent/TASK_QUEUE.md` — check for overlapping work
3. **Read** this track file — find the next `[ ]` task
4. **Read** `conductor/index.md` — confirm workflow and style sources

### Step 1: Understand the Rules
1. **Read** `conductor/workflow.md` — TDD phases (Red/Green/Refactor)
2. **Read** `conductor/code_styleguides/python.md` — Python conventions
3. **Read** `conductor/code_styleguides/agent-improvement.md` — FastAPI routing, Pydantic V2, security

### Step 2: Verify Before Coding
- Run `python -m pytest tests/ -v --tb=short` for clean baseline
- Read existing implementation: `src/backend/podcast_engine.py` (`dub_audio`, `generate_voice_changer`)
- Read frontend: `src/static/dubbing.js`

---

## Phase 1: Dubbing Pipeline Hardening 🌍

> **Why:** The current `dub_audio` method is functional but minimal — no progress tracking, no language auto-detection, no subtitle export.

### Current `dub_audio()` Signature (from `podcast_engine.py` L518-536):
```python
def dub_audio(self, audio_path: str, target_lang: str):
    # 1. Transcribe source audio
    text = self.transcribe_audio(audio_path)
    # 2. Translate (uses model's internal translation)
    # 3. Generate clone voice with translated text
    # Returns: {"waveform": ..., "sample_rate": ..., "text": ...}
```

### Current `generate_voice_changer()` (L337-347):
```python
def generate_voice_changer(self, source_audio, target_profile=None):
    text = self.transcribe_audio(source_audio)
    prompt_items = model.create_voice_clone_prompt(ref_audio=source_path, ref_text=text, x_vector_only_mode=False)
    target_emb = self.get_speaker_embedding(target_profile or {"type": "preset", "value": "Ryan"})
    voice_clone_prompt = {"ref_code": [...], "ref_spk_embedding": [...], "x_vector_only_mode": [False], "icl_mode": [True]}
    wavs, sr = model.generate_voice_clone(text=text, voice_clone_prompt=voice_clone_prompt)
```

### Tasks

- [ ] **1.1 — Auto Language Detection**

  **Step 1: Extract language from `transcribe_audio()` return value.**
  
  Whisper already returns `language` in its result (L119-145). Currently `transcribe_audio()` only returns `text`. Modify to return more:
  ```python
  # In podcast_engine.py L119-145, modify transcribe_audio():
  def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
      """Transcribe audio and return text + detected language."""
      resolved = self._resolve_paths(audio_path)
      source_path = str(resolved[0])
      if VideoEngine.is_video(source_path):
          source_path = self._extract_audio_with_cache(source_path)
      model = get_model("Base")
      result = model.transcribe(source_path)  # Whisper returns {"text": ..., "language": ...}
      return {
          "text": result.get("text", ""),
          "language": result.get("language", "unknown"),
          "segments": result.get("segments", [])  # timestamps per word/segment
      }
  ```

  **⚠️ Breaking change:** `transcribe_audio()` currently returns `str`. Callers (`dub_audio`, `generate_voice_changer`) must be updated:
  ```python
  # In dub_audio (L518):
  result = self.transcribe_audio(audio_path)
  text = result["text"]
  detected_lang = result["language"]
  
  # In generate_voice_changer (L338):
  result = self.transcribe_audio(source_audio)
  text = result["text"] if isinstance(result, dict) else result  # backward compat
  ```

  **Step 2: Add language detection endpoint in `generation.py`:**
  ```python
  @router.post("/detect-language")
  async def detect_language(file: UploadFile = File(...)):
      """Detect language from uploaded audio."""
      engine = server_state.engine
      # Save to temp, transcribe, return language
      temp_path = save_upload(file)
      result = engine.transcribe_audio(temp_path)
      return {"language": result["language"], "text_preview": result["text"][:100]}
  ```

  **Step 3: Call from frontend in `dubbing.js` after upload:**
  ```javascript
  // After file upload succeeds:
  const detectRes = await fetch('/api/generate/detect-language', { method: 'POST', body: formData });
  const detectData = await detectRes.json();
  document.getElementById('dub-detected-lang').textContent = `Detected: ${detectData.language}`;
  document.getElementById('dub-source-lang').value = detectData.language;
  ```

  **Acceptance:** Upload audio → UI shows "Detected: English" before dubbing.

---

- [ ] **1.2 — Dubbing Progress Tracking**

  **Step 1: Create a dubbing-specific background task in `generation.py`:**
  ```python
  def run_dubbing_task(task_id: str, audio_path: str, target_lang: str, voice_profile: dict):
      """Background dubbing task with step-by-step progress."""
      try:
          engine = server_state.engine
          tm = server_state.task_manager
          
          tm.update_task(task_id, progress=10, message="Transcribing source audio...")
          result = engine.transcribe_audio(audio_path)
          text = result["text"]
          source_lang = result["language"]
          
          tm.update_task(task_id, progress=30, message=f"Detected {source_lang}. Translating to {target_lang}...")
          # Translation step (depends on implementation)
          
          tm.update_task(task_id, progress=60, message="Synthesizing dubbed audio...")
          wav, sr = engine.generate_segment(text=translated_text, profile=voice_profile)
          
          tm.update_task(task_id, progress=90, message="Post-processing...")
          # Apply post-processing if needed
          
          tm.update_task(task_id, status=server_state.TaskStatus.COMPLETED, progress=100,
              message="Dubbing complete",
              result={"waveform": wav.tolist(), "sample_rate": sr, "text": translated_text})
      except Exception as e:
          tm.update_task(task_id, status=server_state.TaskStatus.FAILED, error=str(e))
  ```

  **Step 2: Add endpoint:**
  ```python
  @router.post("/dub")
  async def dub_audio_endpoint(request: DubRequest, background_tasks: BackgroundTasks):
      task_id = server_state.task_manager.create_task("dubbing", {"target_lang": request.target_language})
      background_tasks.add_task(run_dubbing_task, task_id, request.audio_path, request.target_language, request.voice_profile)
      return {"task_id": task_id}
  ```

  **Step 3: Wire `dubbing.js` to use `TaskManager.pollTask()`:**
  ```javascript
  // Replace direct fetch with task-based polling:
  const res = await fetch('/api/generate/dub', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ audio_path, target_language, voice_profile })
  });
  const { task_id } = await res.json();
  TaskManager.pollTask(task_id, (task) => {
      statusEl.textContent = `${task.progress}% — ${task.message}`;
  });
  ```

  **Acceptance:** Dubbing task in sidebar. Steps: transcribing → translating → synthesizing → complete.

---

- [ ] **1.3 — Source Audio Preview**

  **Step 1: After file upload in `dubbing.js`, create an audio element:**
  ```javascript
  // After upload response:
  const audioUrl = `/api/voice/uploads/${uploadData.filename}`;
  const previewContainer = document.getElementById('dub-source-preview');
  previewContainer.innerHTML = `
      <audio id="dub-source-player" controls style="width:100%;">
          <source src="${audioUrl}" type="audio/wav">
      </audio>
      <div id="dub-source-waveform" style="height:60px; margin-top:8px;"></div>
  `;
  ```

  **Step 2: (Optional) Add WaveSurfer waveform — only if WaveSurfer is included:**
  ```javascript
  if (window.WaveSurfer) {
      const ws = WaveSurfer.create({
          container: '#dub-source-waveform',
          height: 60, waveColor: '#ccff00', progressColor: '#888',
          barWidth: 2, responsive: true
      });
      ws.load(audioUrl);
  }
  ```

  **Acceptance:** Upload → waveform renders → user can play/pause original.

---

- [ ] **1.4 — Side-by-Side Comparison**

  **Step 1: Add dual player HTML in `index.html` (Dubbing section):**
  ```html
  <div id="dub-comparison" style="display:none; gap:12px;">
      <div class="card" style="flex:1; padding:12px;">
          <label class="label-industrial">ORIGINAL</label>
          <audio id="dub-original-player" controls style="width:100%;"></audio>
      </div>
      <div class="card" style="flex:1; padding:12px;">
          <label class="label-industrial">DUBBED</label>
          <audio id="dub-dubbed-player" controls style="width:100%;"></audio>
      </div>
      <button class="btn btn-primary" onclick="syncPlayDubComparison()">▶ SYNC PLAY</button>
  </div>
  ```

  **Step 2: Sync playback function in `dubbing.js`:**
  ```javascript
  function syncPlayDubComparison() {
      const orig = document.getElementById('dub-original-player');
      const dubbed = document.getElementById('dub-dubbed-player');
      orig.currentTime = 0;
      dubbed.currentTime = 0;
      orig.play();
      dubbed.play();
  }
  ```

  **Acceptance:** Dual waveform view. Sync play button plays both simultaneously.

---

- [ ] **1.5 — Subtitle Export (SRT/VTT)**

  **Step 1: Create `src/backend/utils/subtitles.py`** (shared with Narrated Video track):
  ```python
  def generate_srt_from_segments(segments: list) -> str:
      """Generate SRT from Whisper-style segments with timestamps."""
      entries = []
      for i, seg in enumerate(segments):
          start = _fmt(seg["start"])
          end = _fmt(seg["end"])
          text = seg["text"].strip()
          entries.append(f"{i+1}\n{start} --> {end}\n{text}\n")
      return "\n".join(entries)
  
  def generate_vtt_from_segments(segments: list) -> str:
      """Generate WebVTT from segments."""
      header = "WEBVTT\n\n"
      entries = []
      for i, seg in enumerate(segments):
          start = _fmt_vtt(seg["start"])
          end = _fmt_vtt(seg["end"])
          entries.append(f"{start} --> {end}\n{seg['text'].strip()}\n")
      return header + "\n".join(entries)
  ```

  **Step 2: Add subtitle download endpoint:**
  ```python
  @router.get("/dub/{task_id}/subtitles")
  async def download_subtitles(task_id: str, format: str = "srt"):
      task = server_state.task_manager.get_task(task_id)
      segments = task.result.get("segments", [])
      if format == "vtt":
          content = generate_vtt_from_segments(segments)
          return StreamingResponse(io.BytesIO(content.encode()), media_type="text/vtt")
      else:
          content = generate_srt_from_segments(segments)
          return StreamingResponse(io.BytesIO(content.encode()), media_type="application/x-subrip")
  ```

  **Step 3: Add download buttons after dubbing completes in `dubbing.js`:**
  ```javascript
  `<a href="/api/generate/dub/${task_id}/subtitles?format=srt" download class="btn btn-sm">📥 SRT</a>
   <a href="/api/generate/dub/${task_id}/subtitles?format=vtt" download class="btn btn-sm">📥 VTT</a>`
  ```

  **Acceptance:** After dubbing, download `.srt` file with timestamped translated captions.

---

## Phase 2: Voice Changer (S2S) Enhancement 🔄

> **Why:** The voice changer uses ICL mode but doesn't have UI controls for prosody or emotion.

### Current S2S Flow (from `generate_voice_changer()` L337-347):
```python
# 1. Transcribe source audio → get text
# 2. Create clone prompt from source (ref_code captures prosody via ICL)
# 3. Get target voice embedding
# 4. Generate clone with target embedding + source ref_code
# ICL mode naturally preserves prosody from the source
```

### Tasks

- [x] **2.1 — Wire Prosody Preservation**

  **Step 1: Add `preserve_prosody` flag to `S2SRequest` in `schemas.py`:**
  ```python
  class S2SRequest(BaseModel):
      source_audio: str
      target_voice: Optional[Dict[str, Any]] = None
      preserve_prosody: bool = True   # <-- ADD
      instruct: Optional[str] = None  # <-- ADD: emotion control
  ```

  **Step 2: Modify `generate_voice_changer()` at L337:**
  ```python
  def generate_voice_changer(self, source_audio, target_profile=None, 
                              preserve_prosody=True, instruct=None):
      text = self.transcribe_audio(source_audio)
      if isinstance(text, dict): text = text["text"]  # backward compat
      
      resolved = self._resolve_paths(source_audio)
      source_path = str(resolved[0])
      if VideoEngine.is_video(source_path):
          source_path = self._extract_audio_with_cache(source_path)
      
      model = get_model("Base")
      
      if preserve_prosody:
          # ICL mode: use ref_code from source to capture prosody
          prompt_items = model.create_voice_clone_prompt(
              ref_audio=source_path, ref_text=text, x_vector_only_mode=False)
          target_emb = self.get_speaker_embedding(target_profile or {"type": "preset", "value": "Ryan"})
          
          # Build instruct hint for prosody
          prosody_instruct = instruct or "preserve original rhythm, pacing, and emphasis"
          
          voice_clone_prompt = {
              "ref_code": [prompt_items[0].ref_code],
              "ref_spk_embedding": [target_emb],
              "x_vector_only_mode": [False],
              "icl_mode": [True]
          }
          wavs, sr = model.generate_voice_clone(
              text=text, voice_clone_prompt=voice_clone_prompt, instruct=prosody_instruct)
      else:
          # X-vector only mode: just change the voice, ignore prosody
          target_emb = self.get_speaker_embedding(target_profile or {"type": "preset", "value": "Ryan"})
          prompt_items = model.create_voice_clone_prompt(
              ref_audio=source_path, x_vector_only_mode=True)
          voice_clone_prompt = {
              "ref_spk_embedding": [target_emb],
              "x_vector_only_mode": [True],
              "icl_mode": [False]
          }
          wavs, sr = model.generate_voice_clone(
              text=text, voice_clone_prompt=voice_clone_prompt, instruct=instruct)
      
      return {"waveform": wavs[0], "sample_rate": sr, "text": text}
  ```

  **Step 3: Wire the checkbox in `dubbing.js`:**
  ```javascript
  const preserveProsody = document.getElementById('preserve-prosody').checked;
  // Include in S2S request body:
  body: JSON.stringify({ source_audio: path, target_voice: profile, preserve_prosody: preserveProsody })
  ```

  **Acceptance:** Prosody on → output follows source rhythm. Prosody off → target voice's natural cadence.

---

- [x] **2.2 — Target Voice Preview Before Conversion**

  **Add preview button next to the target voice dropdown in `index.html`:**
  ```html
  <div style="display:flex; gap:8px; align-items:center;">
      <select id="s2s-target-voice" style="flex:1;"><!-- populated by voicelab.js --></select>
      <button class="btn btn-sm btn-secondary" onclick="previewTargetVoice()" title="Preview target voice">
          <i class="fas fa-play"></i>
      </button>
  </div>
  ```

  **Add handler in `dubbing.js`:**
  ```javascript
  async function previewTargetVoice() {
      const voiceId = document.getElementById('s2s-target-voice').value;
      if (!voiceId) return Notification.show("Select a target voice", "warn");
      const profiles = await window.getAllProfiles();
      const profile = profiles[voiceId];
      if (!profile) return;
      const body = { type: profile.type, value: profile.value, name: "Preview" };
      const res = await fetch('/api/voice/preview', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(body)
      });
      const blob = await res.blob();
      const player = document.getElementById('preview-player');
      player.src = URL.createObjectURL(blob);
      player.play();
  }
  ```

  **Acceptance:** Click preview → plays short sample in that voice.

---

- [x] **2.3 — Batch S2S Conversion**

  **Step 1: Support multiple files via drag-and-drop in `dubbing.js`:**
  ```javascript
  // Add drop zone:
  const dropZone = document.getElementById('s2s-drop-zone');
  dropZone.addEventListener('drop', async (e) => {
      e.preventDefault();
      const files = Array.from(e.dataTransfer.files);
      const profile = { type: 'preset', value: document.getElementById('s2s-target-voice').value };
      
      for (const file of files) {
          const formData = new FormData();
          formData.append('file', file);
          const upRes = await fetch('/api/voice/upload', { method: 'POST', body: formData });
          const upData = await upRes.json();
          
          // Submit S2S task for each file
          const res = await fetch('/api/generate/s2s', {
              method: 'POST', headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ source_audio: upData.filename, target_voice: profile })
          });
          const { task_id } = await res.json();
          Notification.show(`Queued: ${file.name}`, "info");
      }
  });
  ```

  **Acceptance:** Drop 5 audio files → all queued with progress in sidebar.

---

- [x] **2.4 — Emotion Instruct for S2S**

  **Use the same `EMOTION_PRESETS` map from Voice Library track:**
  ```javascript
  // Add emotion dropdown in S2S section of index.html:
  `<select id="s2s-emotion">
      <option value="">Neutral</option>
      <option value="happy">😊 Happy</option>
      <option value="sad">😢 Sad</option>
      <option value="angry">😠 Angry</option>
      <option value="excited">🤩 Excited</option>
      <option value="calm">😌 Calm</option>
  </select>`
  
  // When submitting S2S request:
  const emotion = document.getElementById('s2s-emotion').value;
  const instruct = emotion ? EMOTION_PRESETS[emotion] : null;
  body: JSON.stringify({ source_audio, target_voice, preserve_prosody, instruct })
  ```

  **Backend already supports `instruct` via `generate_voice_clone()`** — just pass it through.

  **Acceptance:** Select "Excited" → S2S output has energetic delivery.

---

## Phase 3: Multi-Speaker Dubbing 🎭

> **Why:** Real dubbing involves multiple speakers. Current system treats all audio as single-speaker.

### Tasks

- [ ] **3.1 — Speaker Diarization Integration**

  **⚠️ Dependency: `pyannote-audio`** — ~1GB model download. Must update `requirements.txt` and `conductor/tech-stack.md`.

  **Step 1: Create `src/backend/diarization.py`:**
  ```python
  """Speaker diarization using pyannote-audio."""
  import torch
  from pathlib import Path
  
  _pipeline = None
  
  def get_diarization_pipeline():
      global _pipeline
      if _pipeline is None:
          try:
              from pyannote.audio import Pipeline
              _pipeline = Pipeline.from_pretrained(
                  "pyannote/speaker-diarization-3.1",
                  use_auth_token="YOUR_HF_TOKEN"  # Requires Hugging Face token
              )
              if torch.cuda.is_available():
                  _pipeline = _pipeline.to(torch.device("cuda"))
          except ImportError:
              raise RuntimeError("pyannote-audio not installed. Run: pip install pyannote.audio")
      return _pipeline
  
  def diarize_audio(audio_path: str) -> list:
      """Run speaker diarization. Returns list of segments with speaker labels."""
      pipeline = get_diarization_pipeline()
      diarization = pipeline(audio_path)
      
      segments = []
      for turn, _, speaker in diarization.itertracks(yield_label=True):
          segments.append({
              "start": round(turn.start, 3),
              "end": round(turn.end, 3),
              "speaker": speaker,
              "duration": round(turn.end - turn.start, 3)
          })
      return segments
  ```

  **Step 2: Add diarization endpoint:**
  ```python
  @router.post("/diarize")
  async def diarize_audio_endpoint(request: DubRequest):
      from ..diarization import diarize_audio
      segments = diarize_audio(request.audio_path)
      # Group segments by speaker
      speakers = {}
      for seg in segments:
          speakers.setdefault(seg["speaker"], []).append(seg)
      return {"speakers": speakers, "total_speakers": len(speakers)}
  ```

  **Acceptance:** Upload multi-speaker audio → identifies Speaker 1, Speaker 2, etc.

---

- [ ] **3.2 — Per-Speaker Voice Assignment**

  **Step 1: After diarization, show speaker table in `dubbing.js`:**
  ```javascript
  function renderSpeakerAssignment(speakers) {
      const container = document.getElementById('speaker-assignment');
      const presets = window.state.presets;
      
      container.innerHTML = Object.entries(speakers).map(([spk, segments]) => {
          const totalDuration = segments.reduce((sum, s) => sum + s.duration, 0).toFixed(1);
          return `
          <div class="card" style="padding:12px; margin:8px 0;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                  <strong>${spk}</strong>
                  <span style="opacity:0.6;">${totalDuration}s total</span>
              </div>
              <select class="speaker-voice-select" data-speaker="${spk}">
                  ${presets.map(p => `<option value="${p.id}">${p.name}</option>`).join('')}
              </select>
          </div>`;
      }).join('');
  }
  ```

  **Acceptance:** 3 speakers detected → user assigns Aiden, Serena, Dylan.

---

- [ ] **3.3 — Multi-Speaker Synthesis & Merge**

  **Step 1: Generate each speaker's segments, then merge by timeline:**
  ```python
  def run_multi_speaker_dub_task(task_id, audio_path, target_lang, speaker_voices, diarization):
      engine = server_state.engine
      tm = server_state.task_manager
      
      import librosa
      source_audio, sr = librosa.load(audio_path, sr=24000)
      total_duration = len(source_audio) / sr
      output = np.zeros(int(total_duration * 24000), dtype=np.float32)
      
      speakers = list(speaker_voices.keys())
      for i, speaker in enumerate(speakers):
          tm.update_task(task_id, progress=int(20 + 60 * i / len(speakers)),
              message=f"Dubbing {speaker}...")
          
          segments = diarization[speaker]
          voice_profile = speaker_voices[speaker]
          
          for seg in segments:
              # Extract segment text from transcription
              text = seg.get("text", "")
              if not text: continue
              
              # Generate with assigned voice
              wav, seg_sr = engine.generate_segment(text, profile=voice_profile)
              
              # Place in timeline at original position
              start_sample = int(seg["start"] * 24000)
              end_sample = min(start_sample + len(wav), len(output))
              output[start_sample:end_sample] = wav[:end_sample - start_sample]
      
      return output, 24000
  ```

  **Acceptance:** Final dubbed output has 3 distinct voices matching speaker turns.

---

## Key Files Reference

| File | Purpose | Key Lines |
|------|---------|-----------|
| `src/backend/podcast_engine.py` | `dub_audio()` L518, `generate_voice_changer()` L337, `transcribe_audio()` L119 | Core dubbing/S2S logic |
| `src/backend/api/generation.py` | Generation endpoints, task creation | L1-163 |
| `src/backend/api/schemas.py` | `DubRequest`, `S2SRequest` | L50-65 |
| `src/static/dubbing.js` | Dubbing & S2S frontend logic | Upload, dub trigger, comparison |
| `src/static/index.html` | Dubbing & S2S UI section | Drop zones, language selectors |
| `src/static/task_manager.js` | Sidebar task polling | `TaskManager.pollTask()` |
| `src/backend/diarization.py` | [NEW] pyannote speaker diarization | Phase 3 only |
| `src/backend/utils/subtitles.py` | [NEW/SHARED] SRT/VTT generation | Shared with Video track |

### Qwen3 S2S API Quick Reference
```python
# Voice changer uses ICL mode to transfer voice while preserving prosody:
prompt_items = model.create_voice_clone_prompt(
    ref_audio=source_path, ref_text=transcribed_text, x_vector_only_mode=False)
# ref_code captures the prosody/rhythm from the source audio

# Then generate with target voice embedding:
wavs, sr = model.generate_voice_clone(
    text=transcribed_text,
    voice_clone_prompt={
        "ref_code": [prompt_items[0].ref_code],      # source prosody
        "ref_spk_embedding": [target_embedding],       # target voice
        "x_vector_only_mode": [False],
        "icl_mode": [True]
    },
    instruct="preserve original rhythm"  # optional instruct hint
)
```

