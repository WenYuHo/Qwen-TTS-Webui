# Track: Production Workflow & Export

## Overview
- **Goal:** Elevate the Project Studio from a basic script-to-audio tool into a professional production suite with undo/redo, block-level editing, multi-format export, project templates, and collaborative features.
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

### Step 2: Verify Before Coding
- Read existing code: `src/static/production.js`, `src/static/shared.js` (`CanvasManager`)
- Read API: `src/backend/api/projects.py`, `src/backend/api/generation.py`

---

## Phase 1: Block Editor Power Features ✏️

> **Why:** The production view has basic block rendering but lacks undo, drag-reorder, or per-block regeneration.

### Current `renderBlocks()` (from `production.js` L313-334):
```javascript
renderBlocks() {
    const container = document.getElementById('blocks-container');
    container.innerHTML = window.CanvasManager.blocks.map(b => `
        <div class="card" ...>
            <strong>${b.role.toUpperCase()}</strong>
            <button onclick="CanvasManager.moveBlock('${b.id}', -1)">▲</button>
            <button onclick="CanvasManager.moveBlock('${b.id}', 1)">▼</button>
            <button onclick="CanvasManager.deleteBlock('${b.id}')">🗑</button>
            <!-- PAN slider -->
        </div>
    `).join('');
}
```

### Tasks

- [ ] **1.1 — Undo/Redo System**

  **Step 1: Add undo stack to `CanvasManager` in `shared.js`:**
  ```javascript
  // In shared.js — CanvasManager object:
  const CanvasManager = {
      blocks: [],
      _undoStack: [],    // ADD: array of block snapshots
      _redoStack: [],    // ADD
      _maxHistory: 50,   // ADD: max undo depth
      
      _saveSnapshot() {
          this._undoStack.push(JSON.parse(JSON.stringify(this.blocks)));
          if (this._undoStack.length > this._maxHistory) this._undoStack.shift();
          this._redoStack = [];  // Clear redo on new action
      },
      
      undo() {
          if (this._undoStack.length === 0) return;
          this._redoStack.push(JSON.parse(JSON.stringify(this.blocks)));
          this.blocks = this._undoStack.pop();
          window.ProductionManager?.renderBlocks();
      },
      
      redo() {
          if (this._redoStack.length === 0) return;
          this._undoStack.push(JSON.parse(JSON.stringify(this.blocks)));
          this.blocks = this._redoStack.pop();
          window.ProductionManager?.renderBlocks();
      },
      
      // Modify existing mutation methods to call _saveSnapshot():
      addBlock(role, text) {
          this._saveSnapshot();  // ADD this line at top
          // ... existing addBlock code
      },
      deleteBlock(id) {
          this._saveSnapshot();  // ADD this line at top
          // ... existing deleteBlock code
      },
      moveBlock(id, direction) {
          this._saveSnapshot();  // ADD this line at top
          // ... existing moveBlock code
      },
      updateBlock(id, updates) {
          this._saveSnapshot();  // ADD this line at top
          // ... existing updateBlock code
      },
  };
  ```

  **Step 2: Wire keyboard shortcuts in `app.js`:**
  ```javascript
  document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
          e.preventDefault();
          window.CanvasManager.undo();
      } else if (e.ctrlKey && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
          e.preventDefault();
          window.CanvasManager.redo();
      }
  });
  ```

  **Acceptance:** Add blocks → delete one → Ctrl+Z → restored. Ctrl+Y → deleted again.

---

- [ ] **1.2 — Drag-and-Drop Block Reordering**

  **Step 1: Add `draggable` to block cards in `renderBlocks()` (L317):**
  ```javascript
  renderBlocks() {
      const container = document.getElementById('blocks-container');
      container.innerHTML = window.CanvasManager.blocks.map((b, index) => `
          <div class="card block-card" draggable="true" data-block-id="${b.id}"
               style="margin-bottom:12px; padding:16px; border-left:4px solid var(--accent);
                      background:rgba(255,255,255,0.02); cursor:grab; transition:transform 0.2s;">
              <!-- ... existing block content ... -->
          </div>
      `).join('');
      
      // Wire drag-and-drop after rendering:
      this._initDragDrop(container);
  },
  
  _initDragDrop(container) {
      let draggedId = null;
      
      container.querySelectorAll('.block-card').forEach(card => {
          card.addEventListener('dragstart', (e) => {
              draggedId = card.dataset.blockId;
              card.style.opacity = '0.5';
              e.dataTransfer.effectAllowed = 'move';
          });
          
          card.addEventListener('dragend', () => {
              card.style.opacity = '1';
              container.querySelectorAll('.block-card').forEach(c =>
                  c.classList.remove('drag-over'));
          });
          
          card.addEventListener('dragover', (e) => {
              e.preventDefault();
              e.dataTransfer.dropEffect = 'move';
              card.classList.add('drag-over');
          });
          
          card.addEventListener('dragleave', () => {
              card.classList.remove('drag-over');
          });
          
          card.addEventListener('drop', (e) => {
              e.preventDefault();
              const targetId = card.dataset.blockId;
              if (draggedId && draggedId !== targetId) {
                  window.CanvasManager._saveSnapshot();
                  const blocks = window.CanvasManager.blocks;
                  const fromIdx = blocks.findIndex(b => b.id === draggedId);
                  const toIdx = blocks.findIndex(b => b.id === targetId);
                  const [moved] = blocks.splice(fromIdx, 1);
                  blocks.splice(toIdx, 0, moved);
                  this.renderBlocks();
              }
          });
      });
  },
  ```

  **Step 2: Add CSS for drag feedback in `style.css`:**
  ```css
  .block-card.drag-over {
      border-top: 3px solid var(--accent);
      transform: translateY(2px);
  }
  .block-card[draggable="true"]:active {
      cursor: grabbing;
  }
  ```

  **Acceptance:** Drag block from position 3 to 1 → visual feedback during drag → order persists.

---

- [ ] **1.3 — Per-Block Regeneration**

  **Step 1: Add regenerate button in `renderBlocks()` block template:**
  ```javascript
  `<button class="btn btn-secondary btn-sm" 
       onclick="window.ProductionManager.regenerateBlock('${b.id}')"
       title="Regenerate this block">
      <i class="fas fa-redo"></i>
  </button>`
  ```

  **Step 2: Implement `regenerateBlock()` in `production.js`:**
  ```javascript
  async regenerateBlock(blockId) {
      const block = window.CanvasManager.blocks.find(b => b.id === blockId);
      if (!block) return;
      
      const profiles = await window.getAllProfiles();
      const profile = profiles[block.role];
      if (!profile) return Notification.show("No voice profile for " + block.role, "warn");
      
      try {
          const res = await fetch('/api/generate/segment', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({
                  profiles: [{role: block.role, ...profile}],
                  script: [{role: block.role, text: block.text, language: block.language || 'auto'}]
              })
          });
          const data = await res.json();
          if (data.task_id) {
              Notification.show(`Regenerating block: ${block.role}`, "info");
              const blob = await window.TaskPoller.poll(data.task_id);
              block.audio_url = URL.createObjectURL(blob);
              block.regenerated = true;
              this.renderBlocks();
              Notification.show("Block regenerated", "success");
          }
      } catch (err) { Notification.show("Regeneration failed", "error"); }
  },
  ```

  **Acceptance:** Click regenerate on block 4 → only block 4 re-synthesizes.

---

- [ ] **1.4 — Block Splitting & Merging**

  ```javascript
  splitBlock(blockId, cursorPosition) {
      const block = window.CanvasManager.blocks.find(b => b.id === blockId);
      if (!block) return;
      window.CanvasManager._saveSnapshot();
      
      const text1 = block.text.substring(0, cursorPosition).trim();
      const text2 = block.text.substring(cursorPosition).trim();
      if (!text1 || !text2) return Notification.show("Cannot split here", "warn");
      
      const idx = window.CanvasManager.blocks.indexOf(block);
      block.text = text1;
      window.CanvasManager.blocks.splice(idx + 1, 0, {
          id: 'block_' + Date.now(),
          role: block.role,
          text: text2,
          language: block.language
      });
      this.renderBlocks();
  },
  
  mergeBlocks(blockId1, blockId2) {
      const b1 = window.CanvasManager.blocks.find(b => b.id === blockId1);
      const b2 = window.CanvasManager.blocks.find(b => b.id === blockId2);
      if (!b1 || !b2 || b1.role !== b2.role) return;
      window.CanvasManager._saveSnapshot();
      
      b1.text = b1.text + ' ' + b2.text;
      window.CanvasManager.blocks = window.CanvasManager.blocks.filter(b => b.id !== blockId2);
      this.renderBlocks();
  },
  ```

  **Acceptance:** Split → two blocks. Merge adjacent same-speaker → one block.

---

- [ ] **1.5 — Block Duration Estimation**

  ```javascript
  // Words per minute for estimation (average speaking rate)
  const WPM = 150;
  
  estimateDuration(text) {
      const words = text.trim().split(/\s+/).length;
      return (words / WPM) * 60;  // seconds
  },
  
  // In renderBlocks(), add estimation display:
  const estSeconds = this.estimateDuration(b.text);
  const estLabel = estSeconds < 60 ? `~${Math.round(estSeconds)}s` : `~${Math.round(estSeconds/60)}:${String(Math.round(estSeconds%60)).padStart(2,'0')}`;
  
  // Add in block card HTML:
  `<span style="opacity:0.5; font-size:0.65rem; font-family:var(--font-mono);">${estLabel}</span>`
  
  // Total duration in footer:
  const totalEst = window.CanvasManager.blocks.reduce((sum, b) => sum + this.estimateDuration(b.text), 0);
  document.getElementById('total-duration-est').textContent = `Total: ~${Math.round(totalEst/60)}:${String(Math.round(totalEst%60)).padStart(2,'0')}`;
  ```

  **Acceptance:** Each block shows "~12s". Footer shows "Total: ~2:45".

---

## Phase 2: Multi-Format Export 📦

> **Why:** Currently exports only WAV. Professional users need MP3, FLAC, OGG.

### Tasks

- [ ] **2.1 — Export Format Selector**

  **Step 1: Add dropdown in `index.html` before the Produce button:**
  ```html
  <div class="control-group">
      <label class="label-industrial">EXPORT FORMAT</label>
      <select id="export-format">
          <option value="wav" selected>WAV (Lossless)</option>
          <option value="mp3">MP3 (320kbps)</option>
          <option value="flac">FLAC (Lossless Compressed)</option>
          <option value="ogg">OGG Vorbis</option>
      </select>
  </div>
  ```

  **Step 2: Backend conversion in `podcast_engine.py` (after final mix):**
  ```python
  def convert_format(self, wav_bytes: bytes, target_format: str) -> bytes:
      """Convert WAV bytes to target format using pydub."""
      from pydub import AudioSegment
      import io
      audio = AudioSegment.from_wav(io.BytesIO(wav_bytes))
      output = io.BytesIO()
      if target_format == "mp3":
          audio.export(output, format="mp3", bitrate="320k",
                       tags={"title": "Podcast", "artist": "Qwen-TTS Studio"})
      elif target_format == "flac":
          audio.export(output, format="flac")
      elif target_format == "ogg":
          audio.export(output, format="ogg", codec="libvorbis")
      else:
          return wav_bytes  # Already WAV
      return output.getvalue()
  ```

  **Step 3: Wire in `generatePodcast()` — send format parameter:**
  ```javascript
  const exportFormat = document.getElementById('export-format').value;
  body: JSON.stringify({ ...existingBody, export_format: exportFormat })
  ```

  **Acceptance:** Select MP3 → produce → download is `.mp3` with metadata.

---

- [ ] **2.2 — Chapter Markers**

  ```python
  # In podcast_engine.py, after generating all segments:
  def _generate_chapters(self, script, segment_durations):
      """Generate chapter metadata for podcast."""
      chapters = []
      offset = 0.0
      for item, duration in zip(script, segment_durations):
          chapters.append({
              "title": f"{item['role']} speaks",
              "start": offset,
              "end": offset + duration
          })
          offset += duration
      return chapters
  
  # Embed in M4A using mutagen:
  def _embed_chapters_m4a(self, m4a_path, chapters):
      from mutagen.mp4 import MP4
      audio = MP4(m4a_path)
      audio["\xa9nam"] = ["Podcast"]
      # MP4 chapters via chpl atom
      chaps = [(int(ch["start"] * 1000), ch["title"]) for ch in chapters]
      audio.save()
  ```

  **Acceptance:** Exported M4A has chapters matching speaker blocks.

---

- [ ] **2.3 — Stem Export**

  ```python
  # In podcast_engine.py — add after generate_podcast():
  def export_stems(self, script, profiles) -> dict:
      """Generate individual speaker tracks as separate WAVs."""
      stems = {}  # {speaker_name: np.ndarray}
      for item in script:
          role = item["role"]
          if role not in stems:
              stems[role] = []
          wav, sr = self.generate_segment(item["text"], profiles.get(role, {}))
          stems[role].append(wav)
      
      # Merge per-speaker
      import numpy as np
      result = {}
      for role, wavs in stems.items():
          result[role] = np.concatenate(wavs)
      return result, sr
  ```

  **API endpoint to download as ZIP:**
  ```python
  @router.post("/generate/stems")
  async def export_stems(request: PodcastRequest):
      stems, sr = engine.export_stems(request.script, request.profiles)
      # Create ZIP in memory
      import zipfile, io
      zip_buffer = io.BytesIO()
      with zipfile.ZipFile(zip_buffer, 'w') as zf:
          for role, wav in stems.items():
              wav_bytes = numpy_to_wav_bytes(wav, sr)
              zf.writestr(f"stem_{role}.wav", wav_bytes)
      return StreamingResponse(io.BytesIO(zip_buffer.getvalue()),
          media_type="application/zip",
          headers={"Content-Disposition": "attachment; filename=stems.zip"})
  ```

  **Acceptance:** "Export Stems" → ZIP with `stem_alice.wav`, `stem_bob.wav`.

---

- [ ] **2.4 — Project Bundle Export/Import**

  Already partially implemented — see `exportStudioBundle()` (L134-153). Enhance:
  ```javascript
  // Current exportStudioBundle() calls /api/projects/{name}/export
  // Backend returns a ZIP with project JSON + audio files
  
  // Add import handler:
  async importStudioBundle(file) {
      const formData = new FormData();
      formData.append('bundle', file);
      try {
          const res = await fetch('/api/projects/import', { method: 'POST', body: formData });
          const data = await res.json();
          if (data.name) {
              await this.fetchProjectList();
              document.getElementById('project-select').value = data.name;
              await this.loadProject();
              Notification.show(`Imported: ${data.name}`, "success");
          }
      } catch (err) { Notification.show("Import failed", "error"); }
  }
  ```

  **Acceptance:** Export → share ZIP → import on another machine → everything restored.

---

## Phase 3: Project Templates & Quick Start 🚀

> **Why:** Users facing blank canvas need templates to accelerate production.

### Tasks

- [ ] **3.1 — Built-In Project Templates**

  **Step 1: Create `src/backend/templates/` with JSON files:**
  ```json
  // src/backend/templates/solo_narration.json
  {
      "name": "Solo Narration",
      "description": "Single narrator reading a script",
      "icon": "📖",
      "script_text": "[Narrator]\nWelcome to this narration.\n\n[Narrator]\nLet's begin with our story today...\n\n[Narrator]\nThank you for listening.",
      "profiles": {
          "Narrator": {"type": "preset", "value": "Aiden"}
      },
      "settings": {
          "bgm_mood": "ambient",
          "ducking_level": 0.3,
          "eq_preset": "warm"
      }
  }
  ```

  **Step 2: Add template browsing endpoint:**
  ```python
  @router.get("/projects/templates")
  async def list_templates():
      templates_dir = Path(__file__).parent.parent / "templates"
      templates = []
      for f in templates_dir.glob("*.json"):
          with open(f) as fp:
              data = json.load(fp)
              templates.append({"name": data["name"], "description": data.get("description", ""),
                                "icon": data.get("icon", "📝"), "file": f.stem})
      return {"templates": templates}
  
  @router.get("/projects/templates/{template_name}")
  async def get_template(template_name: str):
      path = Path(__file__).parent.parent / "templates" / f"{template_name}.json"
      if not path.exists(): raise HTTPException(404, "Template not found")
      with open(path) as f: return json.load(f)
  ```

  **Step 3: Frontend template picker:**
  ```javascript
  async showTemplates() {
      const res = await fetch('/api/projects/templates');
      const { templates } = await res.json();
      const modal = document.getElementById('template-modal');
      modal.innerHTML = templates.map(t => `
          <div class="card" style="cursor:pointer; padding:16px;" onclick="ProductionManager.loadTemplate('${t.file}')">
              <span style="font-size:1.5rem;">${t.icon}</span>
              <strong>${t.name}</strong>
              <p style="opacity:0.6; font-size:0.8rem;">${t.description}</p>
          </div>
      `).join('');
      modal.style.display = 'grid';
  }
  ```

  **Acceptance:** New project → template picker → select "Audio Drama" → pre-filled.

---

- [ ] **3.2 — Save As Template**

  ```javascript
  async saveAsTemplate() {
      const name = prompt("Template name:");
      if (!name) return;
      const data = {
          name: name,
          script_text: document.getElementById('script-editor').value,
          profiles: await window.getAllProfiles(),
          settings: { /* ... collect current settings ... */ }
      };
      await fetch(`/api/projects/templates/${name.toLowerCase().replace(/\s+/g, '_')}`, {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(data)
      });
      Notification.show("Template saved", "success");
  }
  ```

---

- [ ] **3.3 — Script Word Count & Reading Time**

  ```javascript
  // Add to production.js, called on script editor input event:
  updateWordCount() {
      const text = document.getElementById('script-editor').value;
      const words = text.trim().split(/\s+/).filter(w => w.length > 0).length;
      const chars = text.length;
      const readingTime = Math.ceil(words / 150);  // 150 WPM average
      const minutes = Math.floor(readingTime);
      const seconds = Math.round((readingTime - minutes) * 60);
      document.getElementById('word-count-display').textContent = 
          `${words} words · ${chars} chars · ~${minutes}:${String(seconds).padStart(2,'0')} reading time`;
  }
  
  // Wire to editor:
  document.getElementById('script-editor').addEventListener('input', () => {
      ProductionManager.updateWordCount();
  });
  ```

  **Acceptance:** As user types, header shows "342 words · ~2:15 reading time".

---

## Phase 4: Timeline & Waveform View 🎚️

> **Why:** Professional audio production requires visual timeline editing.

### Tasks

- [ ] **4.1 — Waveform Rendering Per Block**

  **Step 1: Include WaveSurfer.js in `index.html`:**
  ```html
  <script src="https://unpkg.com/wavesurfer.js@7/dist/wavesurfer.min.js"></script>
  ```

  **Step 2: After synthesis, render waveform in each block:**
  ```javascript
  // In renderBlocks(), for synthesized blocks:
  if (b.audio_url) {
      // Add waveform container in block HTML:
      `<div id="waveform-${b.id}" style="height:40px; margin-top:8px;"></div>`
      
      // Initialize after DOM update:
      requestAnimationFrame(() => {
          const ws = WaveSurfer.create({
              container: `#waveform-${b.id}`,
              height: 40, waveColor: '#ccff00', progressColor: '#666',
              barWidth: 2, cursorWidth: 1, responsive: true
          });
          ws.load(b.audio_url);
          ws.on('click', () => ws.playPause());
      });
  }
  ```

  **Acceptance:** Synthesized block shows waveform. Click to play from that point.

---

- [ ] **4.2 — Unified Timeline View**

  ```javascript
  // Add third view mode in toggleCanvasView():
  toggleCanvasView(view) {
      const draft = document.getElementById('canvas-draft-view');
      const prod = document.getElementById('canvas-production-view');
      const timeline = document.getElementById('canvas-timeline-view');
      // ... hide all, show selected ...
      if (view === 'timeline') {
          this.renderTimeline();
      }
  },
  
  renderTimeline() {
      const container = document.getElementById('timeline-container');
      const totalDuration = window.CanvasManager.blocks.reduce((sum, b) => 
          sum + this.estimateDuration(b.text), 0);
      
      container.innerHTML = `<div class="timeline-track" style="display:flex; height:60px; width:100%; overflow-x:auto;">
          ${window.CanvasManager.blocks.map(b => {
              const dur = this.estimateDuration(b.text);
              const widthPct = (dur / totalDuration * 100).toFixed(1);
              return `<div class="timeline-block" style="width:${widthPct}%; min-width:40px; 
                           background:rgba(204,255,0,0.1); border-right:1px solid var(--accent);
                           padding:4px; font-size:0.6rem; overflow:hidden;">
                  <strong>${b.role}</strong><br>${Math.round(dur)}s
              </div>`;
          }).join('')}
      </div>`;
  },
  ```

  **Acceptance:** TIMELINE view → horizontal layout with proportional block widths.

---

- [ ] **4.3 — Block Trim Controls**

  Uses WaveSurfer Regions plugin:
  ```javascript
  // After waveform loads for a block:
  import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js';
  
  const regions = ws.registerPlugin(RegionsPlugin.create());
  regions.addRegion({
      start: 0, end: ws.getDuration(),
      color: 'rgba(204, 255, 0, 0.1)', drag: false, resize: true
  });
  
  regions.on('region-updated', (region) => {
      block.trim_start = region.start;
      block.trim_end = region.end;
  });
  ```

  **Acceptance:** Drag trim handles → audio boundaries adjust → used in final export.

---

## Key Files Reference

| File | Purpose | Key Lines |
|------|---------|-----------|
| `src/static/production.js` | `generatePodcast` L5, `renderBlocks` L313, `saveProject` L194 | Block rendering, project CRUD |
| `src/static/shared.js` | `CanvasManager` (blocks state), `parseScript` | Block mutations, undo stack |
| `src/static/index.html` | Project Studio UI layout | Export controls, template picker |
| `src/static/style.css` | Drag feedback, timeline, waveform styles | `.drag-over`, `.timeline-block` |
| `src/backend/api/projects.py` | Project CRUD API, template endpoints | [NEW] `/projects/templates` |
| `src/backend/api/generation.py` | Generation + stems export | [MODIFY] add `/generate/stems` |
| `src/backend/podcast_engine.py` | `generate_podcast` L349, `convert_format`, `export_stems` | Audio assembly |

