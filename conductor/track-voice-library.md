# Track: Voice Library & Expressive Control

## Overview
- **Goal:** Transform the voice library from a simple list into a rich, searchable, shareable voice management system with emotion/style controls, voice favorites, tagging, and community sharing.
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
1. **Read** `conductor/workflow.md` — TDD phases
2. **Read** `conductor/code_styleguides/javascript.md` — JS conventions
3. **Read** `conductor/code_styleguides/html-css.md` — Technoid Brutalist UI
4. **Read** `conductor/product-guidelines.md` — Classic Studio aesthetic

### Step 2: Verify Before Coding
- Read existing: `src/static/voicelab.js`, `src/backend/api/voices.py`, `src/backend/config.py` (VOICE_LIBRARY_FILE)

---

## Phase 1: Voice Library Management 📚

> **Why:** Users create multiple voices but can't organize, tag, or find them efficiently.
> The library is a flat list with basic search. No categories, no favorites, no metadata enrichment.

### Current Voice Library Schema (from `voices.py` L103-123)

The current library is stored as a flat JSON file at `VOICE_LIBRARY_FILE`:
```json
{
  "voices": [
    { "name": "My Narrator", "profile": { "type": "clone", "value": "abc123.wav" } },
    { "name": "Deep Design", "profile": { "type": "design", "value": "A deep male..." } }
  ]
}
```

### Tasks

- [ ] **1.1 — Voice Tags & Categories**

  **Goal:** Add tagging and filtering to the voice library.

  **Step 1: Extend the voice library schema**
  
  No Pydantic change needed — the library uses raw JSON dicts. Update the save/load logic to include tags:
  ```json
  {
    "voices": [
      {
        "name": "My Narrator",
        "profile": { "type": "clone", "value": "abc123.wav" },
        "tags": ["narrator", "calm", "male"],
        "category": "narration",
        "created_at": "2026-03-05T12:00:00Z"
      }
    ]
  }
  ```

  **Step 2: Add tag input to save dialog in `voicelab.js`**
  
  Currently `saveVoice(name, profile)` at line 299 pushes `{ name, profile }`. Modify to:
  ```javascript
  async saveVoice(name, profile) {
      const tagsInput = document.getElementById('voice-tags-input')?.value || '';
      const tags = tagsInput.split(',').map(t => t.trim()).filter(Boolean);
      const category = document.getElementById('voice-category-select')?.value || 'general';
      
      const res = await fetch('/api/voice/library');
      const data = await res.json();
      data.voices.push({ 
          name, profile, tags, category,
          created_at: new Date().toISOString()
      });
      // ... save as before
  }
  ```

  **Step 3: Add filter chips to `index.html`** (above `#voice-library-grid`):
  ```html
  <div id="voice-tag-filters" class="tag-filter-bar" style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:12px;">
      <!-- Populated dynamically by voicelab.js -->
  </div>
  ```

  **Step 4: Add tag filtering to `voicelab.js`** (after `renderVoiceLibrary` at line 222):
  ```javascript
  renderTagFilters(voices) {
      const container = document.getElementById('voice-tag-filters');
      if (!container) return;
      const allTags = [...new Set(voices.flatMap(v => v.tags || []))];
      container.innerHTML = allTags.map(tag => 
          `<button class="btn btn-sm tag-chip" onclick="VoiceLabManager.filterByTag('${tag}')">${tag}</button>`
      ).join('');
  },
  filterByTag(tag) {
      const cards = document.querySelectorAll('#voice-library-grid .voice-card');
      cards.forEach(card => {
          const cardTags = card.dataset.tags || '';
          card.style.display = cardTags.includes(tag) ? 'flex' : 'none';
      });
  }
  ```

  **Step 5: Add `data-tags` to voice cards** in `renderVoiceLibrary()` (line 244):
  ```javascript
  html += savedVoices.map(v => `
      <div class="card voice-card" data-tags="${(v.tags||[]).join(',')}" ...>
  ```

  **Acceptance:** Save voice with tags "narrator, calm" → filter by "narrator" → only matching voices shown.

---

- [ ] **1.2 — Voice Favorites**

  **Step 1: Add `favorite` field to voice JSON:**
  ```json
  { "name": "My Narrator", "profile": {...}, "favorite": true }
  ```

  **Step 2: Sort favorites to top in `renderVoiceLibrary()` (line 222):**
  ```javascript
  renderVoiceLibrary(savedVoices, presets) {
      // Sort: favorites first, then alphabetically
      const sorted = [...savedVoices].sort((a, b) => {
          if (a.favorite && !b.favorite) return -1;
          if (!a.favorite && b.favorite) return 1;
          return a.name.localeCompare(b.name);
      });
      // ... render sorted instead of savedVoices
  ```

  **Step 3: Add star button to each voice card** (next to play/delete at line 251):
  ```javascript
  `<button class="btn btn-sm ${v.favorite ? 'btn-accent' : 'btn-secondary'}" 
           onclick="VoiceLabManager.toggleFavorite('${v.name}')" 
           title="Toggle favorite" aria-label="Toggle favorite for ${v.name}">
      <i class="fas fa-star" aria-hidden="true"></i>
  </button>`
  ```

  **Step 4: Add `toggleFavorite` method:**
  ```javascript
  async toggleFavorite(name) {
      const res = await fetch('/api/voice/library');
      const data = await res.json();
      const voice = data.voices.find(v => v.name === name);
      if (voice) voice.favorite = !voice.favorite;
      await fetch('/api/voice/library', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(data)
      });
      this.loadVoiceLibrary();
  }
  ```

  **Acceptance:** Star a voice → it moves to the top. Persists across page reloads.

---

- [ ] **1.3 — Voice Metadata Enrichment**

  **Step 1: Store metadata when saving a voice** (modify `saveVoice` at line 299):
  ```javascript
  data.voices.push({
      name, profile, tags, category,
      created_at: new Date().toISOString(),
      metadata: {
          source_type: profile.type,
          design_prompt: profile.type === 'design' ? profile.value : null,
          ref_duration: profile.type === 'clone' ? window.state.voicelab.refAudioDuration : null,
          icl_mode: profile.type === 'clone' && profile.ref_text ? true : false,
          ref_text: profile.ref_text || null
      }
  });
  ```

  **Step 2: Display metadata on voice cards** (update `renderVoiceLibrary` line 244):
  ```javascript
  const meta = v.metadata || {};
  const metaText = v.profile.type === 'clone' 
      ? `Cloned · ${meta.ref_duration || '?'}s ref${meta.icl_mode ? ' · ICL mode' : ''}`
      : v.profile.type === 'design'
      ? `Designed · ${(meta.design_prompt || '').substring(0, 40)}…`
      : v.profile.type.toUpperCase();
  const dateText = v.created_at ? new Date(v.created_at).toLocaleDateString() : '';
  // Use metaText + dateText in the card HTML
  ```

  **Acceptance:** Voice card shows "Cloned · 12s ref · ICL mode · Mar 5" or "Designed · A calm mature voice…".

---

- [ ] **1.4 — Voice Import/Export**

  **Step 1: Add export endpoint in `voices.py`:**
  ```python
  @router.get("/library/export/{voice_name}")
  async def export_voice(voice_name: str):
      """Export a single voice profile as a downloadable .qwenvoice JSON file."""
      if not VOICE_LIBRARY_FILE.exists():
          raise HTTPException(404, "Voice library not found")
      with open(VOICE_LIBRARY_FILE, "r", encoding="utf-8") as f:
          lib = json.load(f)
      voice = next((v for v in lib.get("voices", []) if v["name"] == voice_name), None)
      if not voice:
          raise HTTPException(404, f"Voice '{voice_name}' not found")
      # Return as downloadable JSON
      content = json.dumps({"version": 1, "voice": voice}, indent=2)
      return StreamingResponse(
          io.BytesIO(content.encode()),
          media_type="application/json",
          headers={"Content-Disposition": f"attachment; filename={voice_name}.qwenvoice"}
      )
  ```

  **Step 2: Add import endpoint:**
  ```python
  @router.post("/library/import")
  async def import_voice(file: UploadFile = File(...)):
      """Import a .qwenvoice file into the library."""
      content = await file.read()
      data = json.loads(content)
      if data.get("version") != 1 or "voice" not in data:
          raise HTTPException(400, "Invalid .qwenvoice file format")
      voice = data["voice"]
      # Load existing library and append
      lib = {"voices": []}
      if VOICE_LIBRARY_FILE.exists():
          with open(VOICE_LIBRARY_FILE, "r", encoding="utf-8") as f:
              lib = json.load(f)
      lib["voices"].append(voice)
      with open(VOICE_LIBRARY_FILE, "w", encoding="utf-8") as f:
          json.dump(lib, f, indent=2)
      return {"status": "imported", "name": voice["name"]}
  ```

  **Step 3: Add export/import buttons to voice cards in `voicelab.js`:**
  ```javascript
  // Export button on each voice card:
  `<button class="btn btn-sm" onclick="VoiceLabManager.exportVoice('${v.name}')" title="Export">
      <i class="fas fa-download"></i>
  </button>`
  
  // Export method:
  async exportVoice(name) {
      window.location.href = `/api/voice/library/export/${encodeURIComponent(name)}`;
  }
  
  // Import: Add file input + button in index.html Voice Library section
  ```

  **Acceptance:** Export "MyNarrator" → downloads `.qwenvoice` file → import → voice appears in library.

---

- [ ] **1.5 — Voice Comparison Mode**

  **Step 1: Add multi-select checkboxes to voice cards:**
  ```javascript
  `<input type="checkbox" class="voice-compare-checkbox" value="${v.name || id}" 
         onchange="VoiceLabManager.updateCompareSelection()" />`
  ```

  **Step 2: Add compare button and logic:**
  ```javascript
  async compareVoices() {
      const selected = [...document.querySelectorAll('.voice-compare-checkbox:checked')]
          .map(cb => cb.value).slice(0, 3);  // Max 3
      if (selected.length < 2) return Notification.show("Select 2-3 voices to compare", "warn");
      
      const text = document.getElementById('custom-preview-text')?.value?.trim() 
          || "The quick brown fox jumps gracefully over the lazy dog.";
      const profiles = await this.getAllProfiles();
      
      for (const name of selected) {
          const profile = profiles[name];
          if (!profile) continue;
          Notification.show(`Playing: ${name}`, "info");
          // Use preview endpoint and wait for playback
          const body = { type: profile.type, value: profile.value, preview_text: text };
          const res = await fetch('/api/voice/preview', {
              method: 'POST', headers: {'Content-Type': 'application/json'},
              body: JSON.stringify(body)
          });
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const player = document.getElementById('preview-player');
          player.src = url;
          await new Promise(resolve => { player.onended = resolve; player.play(); });
          await new Promise(r => setTimeout(r, 500)); // Brief pause between voices
      }
  }
  ```

  **Acceptance:** Select Aiden + Serena + custom voice → click "Compare" → plays same sentence in all three voices.

---

## Phase 2: Expressive & Emotional Control 🎭

> **Why:** Qwen3 `instruct` parameter controls emotion/style, but the UI doesn't expose it.

### Qwen3 Instruct Reference (all pass via `instruct` kwarg):
```python
# These instruct strings are passed to generate_custom_voice(), generate_voice_design(), or generate_voice_clone()
EMOTION_PRESETS = {
    "happy":      "cheerful, warm, upbeat delivery with a smile in the voice",
    "sad":        "somber, melancholic, soft and slow with a heavy tone",
    "angry":      "intense, forceful, sharp and commanding with rising energy",
    "excited":    "enthusiastic, high energy, fast-paced with dynamic pitch variation",
    "calm":       "relaxed, measured, gentle and soothing with even pacing",
    "serious":    "authoritative, steady, professional broadcast tone",
    "whispering": "very soft, hushed, intimate whisper with minimal volume",
    "sarcastic":  "dry, ironic delivery with subtle emphasis and flat intonation",
}
```

### Tasks

- [ ] **2.1 — Emotion Presets**

  **Step 1: Define emotion presets in `voicelab.js`** (add at top of file):
  ```javascript
  const EMOTION_PRESETS = {
      happy:      "cheerful, warm, upbeat delivery with a smile in the voice",
      sad:        "somber, melancholic, soft and slow with a heavy tone",
      angry:      "intense, forceful, sharp and commanding with rising energy",
      excited:    "enthusiastic, high energy, fast-paced with dynamic pitch variation",
      calm:       "relaxed, measured, gentle and soothing with even pacing",
      serious:    "authoritative, steady, professional broadcast tone",
      whispering: "very soft, hushed, intimate whisper with minimal volume",
      sarcastic:  "dry, ironic delivery with subtle emphasis and flat intonation",
  };
  ```

  **Step 2: Add emotion buttons in `index.html`** (Voice Studio section, near preview text):
  ```html
  <div class="control-group">
      <label class="label-industrial">EMOTION</label>
      <div id="emotion-presets" class="emotion-grid" style="display:flex; gap:6px; flex-wrap:wrap;">
          <button class="btn btn-sm emotion-btn active" data-emotion="" onclick="selectEmotion(this)">Neutral</button>
          <button class="btn btn-sm emotion-btn" data-emotion="happy" onclick="selectEmotion(this)">😊 Happy</button>
          <button class="btn btn-sm emotion-btn" data-emotion="sad" onclick="selectEmotion(this)">😢 Sad</button>
          <button class="btn btn-sm emotion-btn" data-emotion="angry" onclick="selectEmotion(this)">😠 Angry</button>
          <button class="btn btn-sm emotion-btn" data-emotion="excited" onclick="selectEmotion(this)">🤩 Excited</button>
          <button class="btn btn-sm emotion-btn" data-emotion="calm" onclick="selectEmotion(this)">😌 Calm</button>
          <button class="btn btn-sm emotion-btn" data-emotion="serious" onclick="selectEmotion(this)">🎙️ Serious</button>
          <button class="btn btn-sm emotion-btn" data-emotion="whispering" onclick="selectEmotion(this)">🤫 Whisper</button>
      </div>
  </div>
  ```

  **Step 3: Wire emotion into preview/generation requests:**
  ```javascript
  function selectEmotion(btn) {
      document.querySelectorAll('.emotion-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      window.state.selectedEmotion = btn.dataset.emotion;
  }
  
  // In previewVoice() at voicelab.js line 333:
  const emotion = window.state.selectedEmotion;
  const body = { type, value, name: "Preview" };
  if (customText) body.preview_text = customText;
  if (emotion && EMOTION_PRESETS[emotion]) {
      body.instruct = EMOTION_PRESETS[emotion];  // <-- ADD (needs schema support)
  }
  ```

  **Step 4: Add `instruct` to `SpeakerProfile` in `schemas.py` (line 4-9):**
  ```python
  class SpeakerProfile(BaseModel):
      role: Optional[str] = None
      type: str
      value: str
      preview_text: Optional[str] = None
      ref_text: Optional[str] = None
      instruct: Optional[str] = None  # <-- ADD
  ```

  **Step 5: Pass instruct in `voices.py` preview endpoint (line 90):**
  ```python
  instruct = request.instruct or "clear speech, natural delivery, steady pace"
  ```

  **Acceptance:** Click "Happy" → preview sounds cheerful. Click "Whisper" → preview is hushed.

---

- [ ] **2.2 — Speaking Rate Control**

  **Step 1: Add rate toggle in `index.html`:**
  ```html
  <div class="control-group">
      <label class="label-industrial">SPEAKING RATE</label>
      <div class="rate-toggle" style="display:flex; gap:4px;">
          <button class="btn btn-sm rate-btn" data-rate="slower" onclick="selectRate(this)">🐢 Slower</button>
          <button class="btn btn-sm rate-btn active" data-rate="normal" onclick="selectRate(this)">Normal</button>
          <button class="btn btn-sm rate-btn" data-rate="faster" onclick="selectRate(this)">🐇 Faster</button>
      </div>
  </div>
  ```

  **Step 2: Map to instruct strings:**
  ```javascript
  const RATE_INSTRUCTS = {
      slower: "speak slowly and deliberately with measured pacing and clear pauses between phrases",
      normal: "",  // No instruct addition
      faster: "speak quickly and energetically with brisk pacing and minimal pauses",
  };
  function selectRate(btn) {
      document.querySelectorAll('.rate-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      window.state.selectedRate = btn.dataset.rate;
  }
  ```

  **Step 3: Combine emotion + rate instruct in preview calls:**
  ```javascript
  // Build combined instruct:
  let instruct = '';
  if (emotion && EMOTION_PRESETS[emotion]) instruct += EMOTION_PRESETS[emotion];
  if (rate && RATE_INSTRUCTS[rate]) instruct += (instruct ? ', ' : '') + RATE_INSTRUCTS[rate];
  if (instruct) body.instruct = instruct;
  ```

  **Acceptance:** "Slower" → noticeably slower. "Faster" → faster paced.

---

- [ ] **2.3 — Per-Block Emotion Override**

  **File:** `src/static/production.js` — `renderBlocks()` function

  **Step 1: Add emotion dropdown to each block in the production canvas:**
  ```javascript
  // Inside the block rendering loop, add per-block emotion selector:
  `<select class="block-emotion" data-block-id="${block.id}" onchange="updateBlockEmotion(this)">
      <option value="">Neutral</option>
      <option value="happy">😊 Happy</option>
      <option value="sad">😢 Sad</option>
      <option value="angry">😠 Angry</option>
      <option value="excited">🤩 Excited</option>
      <option value="calm">😌 Calm</option>
      <option value="serious">🎙️ Serious</option>
  </select>`
  ```

  **Step 2: Pass emotion as `instruct` per script line:**
  
  In `production.js` when building the podcast request, for each block:
  ```javascript
  const blockEmotion = document.querySelector(`.block-emotion[data-block-id="${block.id}"]`)?.value;
  const scriptLine = {
      role: block.role,
      text: block.text,
      language: block.language || 'auto',
      instruct: blockEmotion ? EMOTION_PRESETS[blockEmotion] : null  // <-- ADD
  };
  ```

  **Backend:** Already supported! `ScriptLine` schema (line 18-25 of `schemas.py`) has `instruct: Optional[str] = None`, and `generate_podcast()` already reads `script[i].get("instruct")` at line 379.

  **Acceptance:** Block 1: "Happy" → Block 2: "Sad" → podcast has emotional shifts.

---

- [ ] **2.4 — Emphasis Markers in Script**

  **Step 1: Parse emphasis markers in `src/static/shared.js` `parseScript()`:**
  ```javascript
  // In parseScript(), after extracting line text:
  function extractEmphasis(text) {
      const emphasized = [];
      // Extract **strong** and *emphasis* markers
      text = text.replace(/\*\*(.+?)\*\*/g, (_, word) => { emphasized.push(word); return word; });
      text = text.replace(/\*(.+?)\*/g, (_, word) => { emphasized.push(word); return word; });
      return { cleanText: text, emphasized };
  }
  ```

  **Step 2: Convert to instruct directive:**
  ```javascript
  const { cleanText, emphasized } = extractEmphasis(lineText);
  if (emphasized.length > 0) {
      scriptLine.instruct = (scriptLine.instruct || '') + 
          `, emphasize the words: "${emphasized.join('", "')}"`;
  }
  scriptLine.text = cleanText;
  ```

  **Acceptance:** Script: `Alice: This is *really* important` → instruct includes `emphasize the words: "really"`.

---

- [ ] **2.5 — Pause Control Tags**

  **Step 1: Parse `<pause:Xs>` and `...` in `shared.js` `parseScript()`:**
  ```javascript
  function parsePauses(text) {
      const segments = [];
      // Split on <pause:Xs> tags
      const parts = text.split(/(<pause:[\d.]+s?>)/gi);
      for (const part of parts) {
          const pauseMatch = part.match(/<pause:([\d.]+)s?>/i);
          if (pauseMatch) {
              segments.push({ type: 'pause', duration: parseFloat(pauseMatch[1]) });
          } else if (part.trim()) {
              segments.push({ type: 'text', content: part.trim() });
          }
      }
      // Also handle "..." as 1s pause
      // (split text segments further on "..." )
      return segments;
  }
  ```

  **Step 2: In `podcast_engine.py` `stream_synthesize()`, handle pause segments:**
  ```python
  # When a pause segment is encountered, yield silence:
  if segment_type == 'pause':
      silence = np.zeros(int(sr * pause_duration), dtype=np.float32)
      yield silence, sr
  ```

  **Alternative (simpler):** Use `pause_after` field in `ScriptLine` — already supported! Just set `pause_after: 2.0` for a 2s pause. Parse `<pause:2s>` in the frontend and split into separate script lines with high `pause_after`.

  **Acceptance:** Script: `Alice: Wait for it... <pause:2s> Surprise!` → 2s silence between sentences.

---

## Phase 3: Voice Quality Insights 📈

> **Why:** Users need feedback on their voice library health.

### Tasks

- [ ] **3.1 — Voice Consistency Score**

  **Step 1: Add consistency check endpoint in `voices.py`:**
  ```python
  @router.post("/consistency")
  async def check_voice_consistency(request: SpeakerProfile):
      """Generate 3 samples and compare embeddings for consistency scoring."""
      import torch
      engine = server_state.engine
      profile = {"type": request.type, "value": request.value}
      if request.ref_text:
          profile["ref_text"] = request.ref_text
      
      text = "The quick brown fox jumps gracefully over the lazy dog."
      embeddings = []
      for _ in range(3):
          wav, sr = engine.generate_segment(text, profile=profile)
          # Extract embedding from the generated audio
          model = get_model("Base")
          prompt = model.create_voice_clone_prompt(ref_audio=(wav, sr), x_vector_only_mode=True)
          embeddings.append(prompt[0].ref_spk_embedding)
      
      # Pairwise cosine similarity
      sims = []
      for i in range(len(embeddings)):
          for j in range(i+1, len(embeddings)):
              sim = float(torch.nn.functional.cosine_similarity(
                  embeddings[i].unsqueeze(0), embeddings[j].unsqueeze(0)
              ))
              sims.append(sim)
      
      avg_similarity = sum(sims) / len(sims) * 100  # As percentage
      return {"consistency": round(avg_similarity, 1), "samples": len(embeddings)}
  ```

  **Step 2: Add "Check Consistency" button on voice cards:**
  ```javascript
  `<button class="btn btn-sm" onclick="VoiceLabManager.checkConsistency('${v.profile.type}', '${v.profile.value}')"
           title="Check consistency"><i class="fas fa-chart-bar"></i></button>`
  ```

  **Acceptance:** Voice card shows "Consistency: 94%". Low scores get a warning.

---

- [ ] **3.2 — Reference Audio Quality Indicator**

  **Step 1: Add quality check endpoint in `voices.py`:**
  ```python
  @router.post("/ref-quality")
  async def check_ref_quality(request: SpeakerProfile):
      """Analyze reference audio quality metrics."""
      import librosa
      engine = server_state.engine
      resolved = engine._resolve_paths(request.value)
      audio_path = str(resolved[0])
      
      audio, sr = librosa.load(audio_path, sr=None)
      duration = len(audio) / sr
      rms = float(np.sqrt(np.mean(audio ** 2)))
      peak = float(np.max(np.abs(audio)))
      # Silence percentage
      silence_threshold = 0.01
      silent_frames = np.sum(np.abs(audio) < silence_threshold)
      silence_pct = round(silent_frames / len(audio) * 100, 1)
      # Simple SNR estimate
      noise_floor = np.percentile(np.abs(audio), 10)
      snr = round(20 * np.log10(rms / (noise_floor + 1e-10)), 1)
      
      quality = "good" if (snr > 20 and silence_pct < 50 and peak < 0.99) else "warning"
      return {
          "duration": round(duration, 1), "snr_db": snr,
          "silence_pct": silence_pct, "clipping": peak > 0.99,
          "quality": quality
      }
  ```

  **Acceptance:** Upload ref audio → "Quality: Good — 15s, SNR 35dB, no clipping" or warning.

---

- [ ] **3.3 — Voice Usage Analytics**

  **Step 1: Track usage in `audit_manager` — already logs events!**
  
  Add a counter endpoint in `voices.py`:
  ```python
  @router.get("/usage")
  async def get_voice_usage():
      """Count how often each voice profile has been used."""
      from ..utils import audit_manager
      log = audit_manager.get_log()
      usage = {}
      for entry in log:
          if entry.get("type") == "synthesis":
              profile_type = entry.get("metadata", {}).get("profile_type", "unknown")
              # Use profile value as key (e.g., speaker name or clone path)
              key = entry.get("metadata", {}).get("profile_value", profile_type)
              usage[key] = usage.get(key, 0) + 1
      return {"usage": usage}
  ```

  **Note:** This requires Task 4.1 from the Sound Gen track (quality scoring) to be implemented first, since that's where `audit_manager.log_event()` is called with synthesis metadata.

  **Acceptance:** Voice card shows "Used in 12 projects". Sort by "Most Used".

---

## Key Files Reference

| File | Purpose | Key Lines |
|------|---------|-----------|
| `src/static/voicelab.js` | Voice lab UI: design, clone, mix, library | L222 (`renderVoiceLibrary`), L299 (`saveVoice`), L333 (`previewVoice`), L374 (`filterVoiceLibrary`) |
| `src/static/index.html` | Voice Studio layout, emotion buttons, rate toggle | Voice Library section, Voice Studio controls |
| `src/static/shared.js` | `parseScript()`, `getVoicePreview()` | Script parsing, emphasis/pause extraction |
| `src/static/production.js` | Per-block emotion, block rendering | `renderBlocks()`, `generatePodcast()` |
| `src/backend/api/voices.py` | Voice library CRUD, preview, export/import | L40 (`get_speakers`), L77 (`preview`), L103 (`get_library`), L114 (`save_library`) |
| `src/backend/api/schemas.py` | `SpeakerProfile` (type, value, instruct, ref_text) | L4-9 |
| `src/backend/podcast_engine.py` | Generation with instruct, embedding extraction | L210 (`generate_segment`), L349 (`generate_podcast`) |
| `src/backend/config.py` | `VOICE_LIBRARY_FILE` path | Config constants |

