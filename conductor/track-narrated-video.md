# Track: Narrated Video Production (Qwen-TTS + LTX)

## Overview
- **Goal:** Elevate the narrated video pipeline from basic text→video to a professional-grade multi-scene, multi-voice video production system with audio sync, subtitle overlay, transitions, and batch rendering.
- **Status:** PLANNED
- **Owner:** Any Agent
- **Start Date:** TBD
- **Models:** Qwen3-TTS (audio narration), LTX-2 / LTX-Video (video generation)

---

## ⚠️ AGENT GUARDRAILS — READ FIRST

### Step 0: Memory Check (MANDATORY)
1. **Read** `agent/MEMORY.md` — understand project state and active tracks
2. **Read** `agent/TASK_QUEUE.md` — check for overlapping work
3. **Read** this track file — find the next `[ ]` task
4. **Read** `conductor/index.md` — confirm workflow and style sources

### Step 1: Understand the Stack
1. **Read** `conductor/tech-stack.md` — LTX and video dependencies
2. **Read** `src/backend/engines/ltx_video_engine.py` — LTX model wrapper
3. **Read** `src/backend/api/video.py` — existing video endpoints (generate, narrated, suggest_scene)
4. **Read** `src/backend/video_engine.py` — audio extraction utility

### Step 2: Verify Before Coding
- Run `python -m pytest tests/test_video_dubbing.py -v --tb=short`
- Check GPU availability and LTX model status via `/api/video/status`

---

## Phase 1: Multi-Scene Narrated Videos 🎬

> **Why:** The current narrated video endpoint generates a single LTX clip + single TTS audio. Real video production needs multiple scenes, each with its own prompt and narration.

### Current Architecture (from `video.py` L77-146):
```python
# Current: single scene only
def run_narrated_video_task(task_id, request: NarratedVideoRequest):
    wav, sr = tts_engine.generate_segment(text=request.narration_text, profile=request.voice_profile)
    result = video_engine.generate_narrated_video(prompt=request.prompt, narration_wav=wav, narration_sr=sr, ...)
```

### Tasks

- [x] **1.1 — Multi-Scene Schema**

  **Step 1: Add `VideoScene` model in `schemas.py` (after line 100):**
  ```python
  class VideoScene(BaseModel):
      video_prompt: str
      narration_text: str
      voice_profile: Optional[Dict[str, Any]] = None  # Falls back to request-level profile
      duration_seconds: Optional[float] = None         # Auto-calculated from TTS if None
      transition: Optional[str] = "cut"                # "cut" | "fade" | "dissolve"
      instruct: Optional[str] = None                   # Emotion for this scene's narration
  ```

  **Step 2: Extend `NarratedVideoRequest` (line 88-100):**
  ```python
  class NarratedVideoRequest(BaseModel):
      # --- Keep existing single-scene fields for backward compat ---
      prompt: Optional[str] = None
      narration_text: Optional[str] = None
      voice_profile: Dict[str, Any] = {}
      # --- New multi-scene support ---
      scenes: Optional[List[VideoScene]] = None  # <-- ADD: list of scenes
      subtitle_enabled: bool = False              # <-- ADD: burn subtitles
      subtitle_position: Optional[str] = "bottom" # "top" | "bottom" | "center"
      subtitle_font_size: Optional[int] = 24
      # --- Keep video params ---
      width: Optional[int] = 768
      height: Optional[int] = 512
      num_frames: Optional[int] = 65
      guidance_scale: Optional[float] = 3.5
      num_inference_steps: Optional[int] = 30
      seed: Optional[int] = -1
  ```

  **Backward compat:** If `scenes` is None, construct `[VideoScene(video_prompt=prompt, narration_text=narration_text)]` from the legacy fields.

  **Acceptance:** API accepts both old single-scene format and new `{"scenes": [...]}`.

---

- [x] **1.2 — Sequential Scene Generation**

  **File:** `src/backend/api/video.py`

  **Rewrite `run_narrated_video_task()` (line 77-146):**
  ```python
  def run_narrated_video_task(task_id: str, request: NarratedVideoRequest):
      try:
          video_engine = _get_video_engine()
          tts_engine = server_state.engine
          
          # Backward compat: convert legacy single-scene to scenes list
          scenes = request.scenes or [VideoScene(
              video_prompt=request.prompt,
              narration_text=request.narration_text
          )]
          
          total = len(scenes)
          scene_clips = []  # List of (video_path, audio_path, duration)
          
          for i, scene in enumerate(scenes):
              pct = int(10 + (80 * i / total))
              server_state.task_manager.update_task(task_id, progress=pct,
                  message=f"Scene {i+1}/{total}: Generating narration...")
              
              # 1. Generate TTS for this scene
              profile = scene.voice_profile or request.voice_profile
              wav, sr = tts_engine.generate_segment(
                  text=scene.narration_text, profile=profile,
                  instruct=scene.instruct
              )
              audio_duration = len(wav) / sr
              
              # 2. Calculate video frames to match audio duration
              # LTX at ~25fps: num_frames = duration * 25 + 1
              num_frames = max(9, int(audio_duration * 25) + 1)
              
              server_state.task_manager.update_task(task_id, progress=pct + 5,
                  message=f"Scene {i+1}/{total}: Generating video ({num_frames} frames)...")
              
              # 3. Generate video for this scene
              result = video_engine.generate_narrated_video(
                  prompt=scene.video_prompt,
                  narration_wav=wav, narration_sr=sr,
                  width=request.width, height=request.height,
                  num_frames=num_frames,
                  guidance_scale=request.guidance_scale,
                  num_inference_steps=request.num_inference_steps,
                  seed=request.seed,
              )
              scene_clips.append({
                  "video_path": result.get("video_path"),
                  "duration": audio_duration,
                  "transition": scene.transition or "cut"
              })
          
          # 4. Concatenate scenes if multiple
          if len(scene_clips) > 1:
              final_path = _concat_scenes(scene_clips)
          else:
              final_path = scene_clips[0]["video_path"]
          
          # 5. Generate subtitles if requested
          srt_path = None
          if request.subtitle_enabled:
              srt_path = _generate_multi_scene_srt(scenes, scene_clips)
          
          server_state.task_manager.update_task(task_id,
              status=server_state.TaskStatus.COMPLETED, progress=100,
              message="Narrated video ready",
              result={"video_path": final_path, "srt_path": srt_path, "scenes": total})
      except Exception as e:
          # ... existing error handling
  ```

  **Step 2: Implement `_concat_scenes()` using MoviePy:**
  ```python
  def _concat_scenes(scene_clips: list) -> str:
      """Concatenate multiple video clips with transitions using MoviePy."""
      from moviepy.editor import VideoFileClip, concatenate_videoclips
      
      clips = []
      for sc in scene_clips:
          clip = VideoFileClip(str(VIDEO_OUTPUT_DIR / sc["video_path"]))
          if sc["transition"] == "fade":
              clip = clip.fadein(0.5).fadeout(0.5)
          elif sc["transition"] == "dissolve":
              clip = clip.crossfadein(0.5)
          clips.append(clip)
      
      final = concatenate_videoclips(clips, method="compose")
      output_path = VIDEO_OUTPUT_DIR / f"narrated_{uuid.uuid4()}.mp4"
      final.write_videofile(str(output_path), codec="libx264", audio_codec="aac", logger=None)
      
      # Cleanup individual clips
      for clip in clips:
          clip.close()
      
      return output_path.name
  ```

  **Acceptance:** 3-scene request → one continuous video with 3 distinct visual+audio scenes.

---

- [ ] **1.3 — Scene Transitions**

  Already handled in `_concat_scenes()` above. The `transition` field in `VideoScene` controls MoviePy effects.

  **MoviePy transition options:**
  ```python
  # "cut"     → no effect, clips simply concatenate 
  # "fade"    → clip.fadein(0.5).fadeout(0.5) — black fade between scenes
  # "dissolve" → clip.crossfadein(0.5) — scenes blend into each other
  ```

  **Acceptance:** Scene with `"transition": "fade"` → smooth black fade.

---

- [ ] **1.4 — Multi-Speaker Scene Assignment**

  Already handled by `VideoScene.voice_profile` field. Each scene falls back to the request-level `voice_profile` if none specified.

  In the frontend (`src/static/video.html` or scene editor), each scene card needs a voice dropdown:
  ```javascript
  // For each scene card:
  `<select class="scene-voice" data-scene-idx="${i}">
      <option value="">Default Voice</option>
      ${presets.map(p => `<option value="${p.id}">${p.name} (${p.gender})</option>`).join('')}
  </select>`
  
  // When building request:
  const sceneVoice = document.querySelector(`.scene-voice[data-scene-idx="${i}"]`).value;
  scene.voice_profile = sceneVoice ? { type: 'preset', value: sceneVoice } : null;
  ```

  **Acceptance:** Scene 1: Aiden. Scene 2: Serena. Each uses correct voice.

---

## Phase 2: Audio-Video Sync & Subtitles 📽️

> **Why:** TTS audio duration rarely matches requested video duration. Proper sync is critical.

### Tasks

- [ ] **2.1 — Duration-Aware Audio Pacing**

  Already implemented in Task 1.2 above! The key formula:
  ```python
  # Calculate frames to match TTS audio duration
  audio_duration = len(wav) / sr
  num_frames = max(9, int(audio_duration * 25) + 1)  # LTX runs at ~25fps
  ```

  **LTX frame math:**
  - LTX generates at ~25fps (configurable per model config)
  - `num_frames=65` → ~2.56s video at 25fps
  - `num_frames` must be ≥ 9 (minimum valid for LTX pipeline)
  - Formula: `num_frames = ceil(target_duration_sec * fps) + 1`

  **Acceptance:** TTS generates 8.5s → LTX video is exactly 8.5s.

---

- [x] **2.2 — SRT/ASS Subtitle Overlay**

  **Step 1: Create `src/backend/utils/subtitles.py`:**
  ```python
  """Subtitle generation and burning utilities."""
  import re
  from pathlib import Path
  
  def generate_srt(scenes: list, scene_durations: list) -> str:
      """Generate SRT subtitle content from multi-scene data."""
      entries = []
      offset = 0.0
      for i, (scene, duration) in enumerate(zip(scenes, scene_durations)):
          text = scene.narration_text
          # Split into sentences for finer-grained subtitles
          sentences = re.split(r'(?<=[.!?])\s+', text)
          sentence_duration = duration / max(len(sentences), 1)
          for j, sentence in enumerate(sentences):
              start = offset + j * sentence_duration
              end = start + sentence_duration
              entries.append(f"{len(entries)+1}\n{_fmt(start)} --> {_fmt(end)}\n{sentence}\n")
          offset += duration
      return "\n".join(entries)
  
  def _fmt(seconds: float) -> str:
      ms = int((seconds % 1) * 1000)
      s = int(seconds % 60)
      m = int((seconds // 60) % 60)
      h = int(seconds // 3600)
      return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
  
  def burn_subtitles(video_path: str, srt_path: str, position: str = "bottom",
                     font_size: int = 24, output_path: str = None) -> str:
      """Burn SRT subtitles into video using MoviePy TextClip."""
      from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
      
      video = VideoFileClip(video_path)
      # Parse SRT
      with open(srt_path, 'r') as f:
          srt_content = f.read()
      
      subtitle_clips = _parse_srt_to_clips(srt_content, video.size, position, font_size)
      final = CompositeVideoClip([video] + subtitle_clips)
      
      out = output_path or video_path.replace('.mp4', '_subtitled.mp4')
      final.write_videofile(out, codec='libx264', audio_codec='aac', logger=None)
      video.close()
      return out
  ```

  **Step 2: Integrate in `run_narrated_video_task()` (after scene concatenation):**
  ```python
  if request.subtitle_enabled:
      from ..utils.subtitles import generate_srt, burn_subtitles
      srt_content = generate_srt(scenes, [sc["duration"] for sc in scene_clips])
      srt_path = VIDEO_OUTPUT_DIR / f"{Path(final_path).stem}.srt"
      with open(srt_path, "w") as f:
          f.write(srt_content)
      # Optionally burn into video:
      final_path = burn_subtitles(
          str(VIDEO_OUTPUT_DIR / final_path), str(srt_path),
          position=request.subtitle_position or "bottom",
          font_size=request.subtitle_font_size or 24
      )
  ```

  **Acceptance:** Generated video has burned-in subtitles synced with narration.

---

- [ ] **2.3 — Subtitle Style Options**

  Already handled by schema fields added in Task 1.1:
  ```python
  subtitle_enabled: bool = False
  subtitle_position: Optional[str] = "bottom"  # "top" | "bottom" | "center"
  subtitle_font_size: Optional[int] = 24
  ```

  **Frontend: Add controls in video section of `index.html`:**
  ```html
  <div class="control-group" id="subtitle-options">
      <label><input type="checkbox" id="subtitle-enabled" /> Enable Subtitles</label>
      <select id="subtitle-position">
          <option value="bottom" selected>Bottom</option>
          <option value="top">Top</option>
          <option value="center">Center</option>
      </select>
      <select id="subtitle-font-size">
          <option value="18">Small</option>
          <option value="24" selected>Medium</option>
          <option value="32">Large</option>
      </select>
  </div>
  ```

  **Acceptance:** Select options → subtitles render at chosen position/size.

---

- [ ] **2.4 — Audio-Only Export Mode**

  **Step 1: Add `audio_only` flag to `NarratedVideoRequest`:**
  ```python
  audio_only: bool = False  # Skip LTX video, export audio only
  ```

  **Step 2: Shortcut in `run_narrated_video_task()`:**
  ```python
  if request.audio_only:
      # Skip video generation entirely — just produce narration audio
      all_wavs = []
      for scene in scenes:
          wav, sr = tts_engine.generate_segment(scene.narration_text, profile=scene.voice_profile or request.voice_profile)
          all_wavs.append(wav)
      # Concatenate all audio
      combined = np.concatenate(all_wavs)
      audio_path = VIDEO_OUTPUT_DIR / f"narration_{uuid.uuid4()}.wav"
      sf.write(str(audio_path), combined, sr)
      server_state.task_manager.update_task(task_id,
          status=server_state.TaskStatus.COMPLETED, progress=100,
          result={"audio_path": audio_path.name, "audio_only": True})
      return
  ```

  **Acceptance:** Toggle audio-only → WAV export only (much faster, no GPU for LTX).

---

## Phase 3: Video Production Features 🎥

> **Why:** Professional video needs batch rendering, prompt enhancement, and preview before committing.

### Tasks

- [ ] **3.1 — Scene Preview (Thumbnail Only)**

  **Step 1: Add preview endpoint in `video.py`:**
  ```python
  @router.post("/preview-scene")
  async def preview_scene(request: VideoGenerationRequest, background_tasks: BackgroundTasks):
      """Generate a single-frame thumbnail preview of a scene."""
      engine = _get_video_engine()
      if not engine.available:
          return {"error": "LTX-2 not available"}
      # Override to 1 frame for fast preview
      request.num_frames = 1
      task_id = server_state.task_manager.create_task("scene_preview", {"prompt": request.prompt[:50]})
      background_tasks.add_task(run_video_generation_task, task_id, request)
      return {"task_id": task_id}
  ```

  **Note:** LTX with `num_frames=1` generates a single image. Some LTX pipeline versions require `num_frames >= 9`. If so, generate 9 frames and extract frame 1 as thumbnail:
  ```python
  # Extract first frame as thumbnail:
  from moviepy.editor import VideoFileClip
  clip = VideoFileClip(video_path)
  clip.save_frame(thumbnail_path, t=0)
  ```

  **Acceptance:** Click "Preview" → thumbnail in <5 seconds.

---

- [ ] **3.2 — Prompt Architect Enhancement**

  **File:** `src/backend/api/video.py` — `suggest_video_scene()` (line 173-270)

  **Enhance the existing template engine** with:
  
  1. **More atmosphere keywords:** Add `"tutorial"`, `"documentary"`, `"comedy"`, `"romantic"`, `"action"` to the `atmospheres` dict (line 197-209):
  ```python
  "documentary": "high-contrast documentary style, handheld camera, natural lighting, authentic textures",
  "tutorial":    "clean studio setup, soft even lighting, professional presenter framing, minimal distractions",
  "comedy":      "bright colorful setting, warm playful lighting, wide comedic framing, exaggerated expressions",
  "romantic":    "soft warm tones, golden hour backlighting, shallow depth of field, intimate close-ups",
  "action":      "dynamic camera movement, high-speed tracking, explosive lighting, adrenaline-pumping visuals",
  ```

  2. **Add character descriptions based on keywords:**
  ```python
  characters = {
      "person": "medium shot of a person",
      "scientist": "focused scientist in lab coat, examining equipment",
      "teacher": "friendly teacher gesturing towards a whiteboard",
      "narrator": "professional narrator seated at a desk, looking at camera",
  }
  ```

  3. **Add LTX-2 best practice suffix:** Always append:
  ```python
  prompt += ", best quality, 4K, HDR, no watermark, no text overlay"
  ```

  **Acceptance:** "a scientist discovers something" → rich cinematic prompt with angles, lighting, character desc.

---

- [ ] **3.3 — Batch Video Rendering Queue**

  **Step 1: Add batch endpoint:**
  ```python
  @router.post("/narrated/batch")
  async def batch_narrated_videos(requests: List[NarratedVideoRequest], background_tasks: BackgroundTasks):
      """Submit multiple narrated video jobs."""
      engine = _get_video_engine()
      if not engine.available:
          return {"error": "LTX-2 not available"}
      
      task_ids = []
      for i, req in enumerate(requests):
          task_id = server_state.task_manager.create_task(
              "narrated_video", {"prompt": req.prompt[:50], "batch_index": i}
          )
          background_tasks.add_task(run_narrated_video_task, task_id, req)
          task_ids.append(task_id)
      
      return {"task_ids": task_ids, "total": len(task_ids)}
  ```

  **Frontend:** Show all tasks in the sidebar `task_manager.js` — each appears with individual progress.

  **Acceptance:** Submit 5 scenes → all appear in sidebar with progress. GPU processes sequentially.

---

- [ ] **3.4 — Video Resolution & Aspect Ratio**

  **Step 1: Define resolution presets in `schemas.py`:**
  ```python
  RESOLUTION_PRESETS = {
      "landscape_hd":  {"width": 768, "height": 512},   # 3:2 standard
      "landscape_16_9": {"width": 848, "height": 480},  # 16:9
      "portrait_9_16": {"width": 480, "height": 848},   # 9:16 (vertical)
      "square":        {"width": 512, "height": 512},   # 1:1
  }
  ```

  **Step 2: Add dropdown in `video.html` or `index.html`:**
  ```html
  <div class="control-group">
      <label class="label-industrial">ASPECT RATIO</label>
      <select id="video-aspect-ratio">
          <option value="landscape_hd" selected>Landscape HD (3:2)</option>
          <option value="landscape_16_9">Landscape 16:9</option>
          <option value="portrait_9_16">Portrait 9:16</option>
          <option value="square">Square 1:1</option>
      </select>
  </div>
  ```

  **Step 3: Frontend reads preset and sets width/height in request:**
  ```javascript
  const preset = RESOLUTION_PRESETS[document.getElementById('video-aspect-ratio').value];
  requestBody.width = preset.width;
  requestBody.height = preset.height;
  ```

  **LTX constraint note:** Width and height must be divisible by 32. All presets above meet this.

  **Acceptance:** Select "9:16 Portrait" → generated video is vertical.

---

## Key Files Reference

| File | Purpose | Key Lines |
|------|---------|-----------|
| `src/backend/api/video.py` | Video endpoints: generate, narrated, suggest, serve | L14 (`_get_video_engine`), L77 (`run_narrated_video_task`), L173 (`suggest_scene`) |
| `src/backend/engines/ltx_video_engine.py` | LTX pipeline wrapper | L136 (`generate_video`), L187 (`generate_narrated_video`), L271 (`get_status`) |
| `src/backend/api/schemas.py` | `VideoGenerationRequest`, `NarratedVideoRequest` | L76-100 |
| `src/backend/video_engine.py` | `extract_audio()`, `is_video()` | L1-37 |
| `src/static/video.html` | Video production UI | Scene editor, preview controls |
| `src/static/production.js` | Frontend: `suggestVideoScene()` | Scene suggest button handler |

### LTX Engine API Quick Reference

```python
# Initialize (lazy-loaded via _get_video_engine()):
engine = LTXVideoEngine()

# Generate video only:
result = engine.generate_video(
    prompt: str, width=768, height=512, num_frames=65,
    guidance_scale=3.5, num_inference_steps=30, seed=-1
)
# Returns: {"path": str, "filename": str, "video_path": str}

# Generate narrated video (video + audio combined):
result = engine.generate_narrated_video(
    prompt: str, narration_wav: np.ndarray, narration_sr: int,
    width=768, height=512, num_frames=65, ...
)
# Returns: {"video_path": str, "duration": float}

# Check availability:
status = engine.get_status()  # {"available": bool, ...}
```

