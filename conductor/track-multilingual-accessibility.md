# Track: Multilingual & Accessibility

## Overview
- **Goal:** Fully leverage Qwen3-TTS's 10-language capability, add UI internationalization, and ensure WCAG accessibility compliance across the entire studio interface.
- **Status:** PLANNED
- **Owner:** Any Agent
- **Start Date:** TBD
- **Models:** Qwen3-TTS supports: Chinese, English, Japanese, Korean, German, French, Russian, Portuguese, Spanish, Italian + Chinese dialects (Cantonese, Hokkien, Sichuanese, etc.)

---

## ⚠️ AGENT GUARDRAILS — READ FIRST

### Step 0: Memory Check (MANDATORY)
1. **Read** `agent/MEMORY.md` — understand project state and active tracks
2. **Read** `agent/TASK_QUEUE.md` — check for overlapping work
3. **Read** this track file — find the next `[ ]` task
4. **Read** `conductor/index.md` — confirm workflow and style sources

### Step 1: Understand Language Support
1. **Read** `src/backend/qwen_tts/inference/qwen3_tts_model.py` — `_supported_languages_set()` method
2. **Read** `src/static/index.html` — current language selectors
3. **Read** `src/backend/podcast_engine.py` — `language` parameter flow

---

## Phase 1: Full 10-Language Support 🌍

> **Why:** Qwen3-TTS supports 10 languages + Chinese dialects, but the UI only shows a few options.

### Qwen3-TTS Language Support (from `qwen3_tts_model.py`):
```python
# _supported_languages_set() returns:
{"zh", "en", "ja", "ko", "de", "fr", "ru", "pt", "es", "it"}
# Chinese dialects supported via language tags:
# "yue" (Cantonese), "min" (Hokkien), "sc" (Sichuanese), etc.
```

### Tasks

- [x] **1.1 — Enumerate All Supported Languages**

  **Step 1: Add `/api/system/languages` endpoint in `system.py`:**
  ```python
  @router.get("/languages")
  async def get_supported_languages():
      """Return all languages supported by the loaded model."""
      from ..qwen_tts.inference import get_model
      try:
          model = get_model("Base")
          languages = model.get_supported_languages()
          # Map ISO codes to display names
          LANG_NAMES = {
              "zh": "Chinese (中文)", "en": "English", "ja": "Japanese (日本語)",
              "ko": "Korean (한국어)", "de": "German (Deutsch)", "fr": "French (Français)",
              "ru": "Russian (Русский)", "pt": "Portuguese (Português)",
              "es": "Spanish (Español)", "it": "Italian (Italiano)"
          }
          return {
              "languages": [
                  {"code": lang, "name": LANG_NAMES.get(lang, lang)}
                  for lang in sorted(languages)
              ],
              "dialects": {
                  "zh": [
                      {"code": "yue", "name": "Cantonese (粵語)"},
                      {"code": "min", "name": "Hokkien (閩南語)"},
                      {"code": "sc", "name": "Sichuanese (四川話)"},
                      {"code": "sx", "name": "Shaanxi (陝西話)"},
                      {"code": "wu", "name": "Wu (吳語)"},
                      {"code": "bj", "name": "Beijing (北京話)"},
                  ]
              }
          }
      except Exception:
          return {"languages": [{"code": "en", "name": "English"}], "dialects": {}}
  ```

  **Step 2: Cache result in `server_state` on startup:**
  ```python
  # In main.py startup event:
  @app.on_event("startup")
  async def cache_languages():
      server_state.supported_languages = await get_supported_languages()
  ```

  **Acceptance:** `GET /api/system/languages` → 10 languages + 6 Chinese dialects.

---

- [x] **1.2 — Update All Language Dropdowns**

  **Step 1: Create shared language loader in `shared.js`:**
  ```javascript
  // In shared.js:
  async function loadLanguages() {
      if (window._languages) return window._languages;
      const res = await fetch('/api/system/languages');
      const data = await res.json();
      window._languages = data;
      return data;
  }
  
  function populateLanguageDropdown(selectId, includeAuto = true) {
      const select = document.getElementById(selectId);
      if (!select || !window._languages) return;
      select.innerHTML = '';
      if (includeAuto) select.innerHTML += '<option value="auto">Auto Detect</option>';
      window._languages.languages.forEach(lang => {
          select.innerHTML += `<option value="${lang.code}">${lang.name}</option>`;
      });
  }
  ```

  **Step 2: Call on page load for every language dropdown:**
  ```javascript
  // In app.js init:
  await loadLanguages();
  populateLanguageDropdown('dub-source-lang', false);    // Dubbing source
  populateLanguageDropdown('dub-target-lang', false);    // Dubbing target
  populateLanguageDropdown('preview-language', true);     // Voice preview
  populateLanguageDropdown('block-language', true);       // Per-block in production
  ```

  **Acceptance:** All dropdowns show 10 languages dynamically. Adding a language to the model auto-updates UI.

---

- [ ] **1.3 — Per-Block Language Selection**

  **Step 1: Add language dropdown to each block in `renderBlocks()` (production.js L317):**
  ```javascript
  // In the block card template:
  `<select class="block-lang-select" data-block-id="${b.id}" style="width:80px; font-size:0.65rem;"
       onchange="window.CanvasManager.updateBlock('${b.id}', {language: this.value})">
      <option value="auto" ${(b.language || 'auto') === 'auto' ? 'selected' : ''}>Auto</option>
      ${(window._languages?.languages || []).map(l =>
          `<option value="${l.code}" ${b.language === l.code ? 'selected' : ''}>${l.code.toUpperCase()}</option>`
      ).join('')}
  </select>`
  ```

  **Step 2: Pass language per-block in `generatePodcast()` (L33-37):**
  ```javascript
  // Already wired! Each block already has `language: b.language || 'auto'`
  script = window.CanvasManager.blocks.map(b => ({
      role: b.role,
      text: b.text,
      language: b.language || 'auto',  // This already exists at L36
      pause_after: b.pause_after || 0.5
  }));
  ```

  **Acceptance:** Block 1: English. Block 2: Japanese → podcast output correct per-block.

---

- [ ] **1.4 — Chinese Dialect Support**

  **Step 1: Add dialect sub-menu when "Chinese" selected:**
  ```javascript
  // Listen for language change:
  function handleLanguageChange(selectEl) {
      const siblingDialect = selectEl.parentElement.querySelector('.dialect-select');
      if (selectEl.value === 'zh' && window._languages?.dialects?.zh) {
          if (!siblingDialect) {
              const dialectSelect = document.createElement('select');
              dialectSelect.className = 'dialect-select';
              dialectSelect.style.cssText = 'width:100px; font-size:0.65rem; margin-left:4px;';
              dialectSelect.innerHTML = '<option value="">Mandarin (default)</option>' +
                  window._languages.dialects.zh.map(d =>
                      `<option value="${d.code}">${d.name}</option>`).join('');
              selectEl.after(dialectSelect);
          }
      } else if (siblingDialect) {
          siblingDialect.remove();
      }
  }
  ```

  **Step 2: Pass dialect to backend as language variant:**
  ```python
  # In podcast_engine.py generate_segment():
  language = item.get("language", "auto")
  dialect = item.get("dialect")
  if dialect:
      language = dialect  # e.g., "yue" for Cantonese — passed directly to model
  ```

  **Model note:** Test whether Qwen3-TTS accepts dialect codes directly or via `instruct`. Some may need `instruct="speak in Cantonese dialect"`.

  **Acceptance:** Select "Cantonese" → synthesis uses Cantonese pronunciation.

---

- [ ] **1.5 — Code-Switching Detection**

  ```python
  # In podcast_engine.py, add helper:
  import re
  
  def detect_language_segments(text: str) -> list:
      """Detect mixed-language segments in text."""
      # Simple heuristic: CJK characters vs Latin
      CJK_RANGES = r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]'
      segments = []
      current_type = None
      current_text = []
      
      for char in text:
          is_cjk = bool(re.match(CJK_RANGES, char))
          char_type = 'cjk' if is_cjk else 'latin'
          
          if char_type != current_type and current_text:
              segments.append({
                  "text": ''.join(current_text).strip(),
                  "type": current_type
              })
              current_text = []
          current_type = char_type
          current_text.append(char)
      
      if current_text:
          segments.append({"text": ''.join(current_text).strip(), "type": current_type})
      
      return [s for s in segments if s["text"]]
  ```

  **Model note:** Qwen3-TTS may handle mixed-language natively. Test before using splitting:
  ```python
  # Test: does "Hello, 你好" produce correct bilingual output without splitting?
  # If yes: skip splitting, just pass to model directly
  # If no: split and synthesize per-segment, then concatenate
  ```

  **Acceptance:** "Hello, 你好世界" → auto-detects and synthesizes appropriately.

---

## Phase 2: UI Internationalization (i18n) 🏳️

> **Why:** The studio UI is English-only. For a global audience, the interface should support multiple languages.

### Tasks

- [x] **2.1 — Extract UI Strings**

  **Step 1: Create `src/static/translations/en.json`:**
  ```json
  {
      "tabs": {
          "voicelab": "VOICE LAB",
          "studio": "PROJECT STUDIO",
          "dubbing": "DUBBING / S2S",
          "system": "SYSTEM"
      },
      "voicelab": {
          "design": {
              "title": "VOICE DESIGN",
              "prompt_label": "VOICE PROMPT",
              "prompt_placeholder": "Describe your ideal voice..."
          },
          "preview": {
              "button": "PREVIEW",
              "loading": "Generating..."
          },
          "library": {
              "title": "VOICE LIBRARY",
              "search": "Search voices...",
              "favorites": "Favorites",
              "all": "All Voices"
          }
      },
      "studio": {
          "draft": "DRAFT",
          "production": "PRODUCTION",
          "produce": "PRODUCE PODCAST",
          "save": "SAVE PROJECT",
          "load": "LOAD PROJECT"
      },
      "dubbing": {
          "upload": "Upload audio file",
          "target_lang": "TARGET LANGUAGE",
          "dub_button": "DUB AUDIO",
          "s2s_title": "VOICE CHANGER (S2S)"
      },
      "common": {
          "cancel": "Cancel",
          "confirm": "Confirm",
          "error": "Error",
          "success": "Success",
          "loading": "Loading..."
      }
  }
  ```

  **Step 2: Audit all hardcoded strings in `index.html`** — replace text content with `data-i18n` attributes:
  ```html
  <!-- Before: -->
  <button>PRODUCE PODCAST</button>
  <!-- After: -->
  <button data-i18n="studio.produce">PRODUCE PODCAST</button>
  ```

  **Acceptance:** Every visible UI string has a `data-i18n` key. English JSON serves as reference.

---

- [x] **2.2 — i18n Loading System**

  **Create `src/static/i18n.js`:**
  ```javascript
  const I18n = {
      translations: {},
      currentLang: 'en',
      
      async load(lang = 'en') {
          try {
              const res = await fetch(`/static/translations/${lang}.json`);
              if (!res.ok) throw new Error(`No translation for ${lang}`);
              this.translations = await res.json();
              this.currentLang = lang;
              this.apply();
          } catch (err) {
              console.warn(`i18n: Failed to load ${lang}, falling back to en`);
              if (lang !== 'en') await this.load('en');
          }
      },
      
      t(key) {
          const parts = key.split('.');
          let value = this.translations;
          for (const part of parts) {
              value = value?.[part];
              if (value === undefined) return key;  // Fallback to key
          }
          return value;
      },
      
      apply() {
          document.querySelectorAll('[data-i18n]').forEach(el => {
              const key = el.getAttribute('data-i18n');
              const translated = this.t(key);
              if (translated !== key) {
                  if (el.tagName === 'INPUT') {
                      el.placeholder = translated;
                  } else {
                      el.textContent = translated;
                  }
              }
          });
      },
      
      async switchTo(lang) {
          await this.load(lang);
          localStorage.setItem('ui_language', lang);
      }
  };
  
  // Auto-load saved language on startup:
  document.addEventListener('DOMContentLoaded', () => {
      const saved = localStorage.getItem('ui_language') || 'en';
      I18n.load(saved);
  });
  
  export { I18n };
  ```

  **Acceptance:** `I18n.t("voicelab.design.title")` → "VOICE DESIGN" in English.

---

- [x] **2.3 — Chinese Translation**

  **Create `src/static/translations/zh.json`:**
  ```json
  {
      "tabs": {
          "voicelab": "语音实验室",
          "studio": "项目工作室",
          "dubbing": "配音 / 变声",
          "system": "系统"
      },
      "voicelab": {
          "design": {
              "title": "语音设计",
              "prompt_label": "语音提示",
              "prompt_placeholder": "描述您理想的声音..."
          },
          "preview": { "button": "预览", "loading": "生成中..." },
          "library": {
              "title": "语音库",
              "search": "搜索声音...",
              "favorites": "收藏",
              "all": "所有声音"
          }
      },
      "studio": {
          "draft": "草稿", "production": "制作",
          "produce": "生成播客", "save": "保存项目", "load": "加载项目"
      },
      "dubbing": {
          "upload": "上传音频文件", "target_lang": "目标语言",
          "dub_button": "配音", "s2s_title": "变声器 (S2S)"
      },
      "common": {
          "cancel": "取消", "confirm": "确认", "error": "错误",
          "success": "成功", "loading": "加载中..."
      }
  }
  ```

  **Acceptance:** Switch to Chinese → entire UI renders in Chinese.

---

- [x] **2.4 — Language Switcher**

  **Add toggle in `index.html` header:**
  ```html
  <div id="lang-switcher" style="display:flex; gap:4px;">
      <button class="btn btn-sm" onclick="I18n.switchTo('en')"
              style="opacity: I18n.currentLang === 'en' ? 1 : 0.5;">EN</button>
      <button class="btn btn-sm" onclick="I18n.switchTo('zh')"
              style="opacity: I18n.currentLang === 'zh' ? 1 : 0.5;">中文</button>
  </div>
  ```

  **Better approach — reactive button styling:**
  ```javascript
  // After I18n.apply(), update switcher buttons:
  document.querySelectorAll('#lang-switcher button').forEach(btn => {
      const lang = btn.textContent === '中文' ? 'zh' : 'en';
      btn.style.opacity = lang === I18n.currentLang ? '1' : '0.5';
      btn.style.borderColor = lang === I18n.currentLang ? 'var(--accent)' : 'transparent';
  });
  ```

  **Acceptance:** Click 中文 → UI switches. Refresh → persists via localStorage.

---

## Phase 3: Accessibility (WCAG 2.1 AA) ♿

> **Why:** Professional tools must be accessible. The Technoid Brutalist dark theme may have contrast issues.

### Tasks

- [x] **3.1 — Color Contrast Audit**

  **Step 1: Identify all text/background combinations in `style.css`:**
  ```css
  /* Current palette from style.css: */
  --bg: #080808;           /* Onyx background */
  --accent: #ccff00;       /* Volt accent */
  --text-primary: #e8e8e8; /* Light grey text */
  --text-secondary: #888;  /* Medium grey text — CHECK THIS */
  --surface: #141414;      /* Card backgrounds */
  
  /* Contrast ratios (WCAG AA requires 4.5:1 for normal text):
   * #ccff00 on #080808 = 12.8:1 ✅
   * #e8e8e8 on #080808 = 16.5:1 ✅
   * #888888 on #080808 = 5.0:1  ✅ (barely passes)
   * #888888 on #141414 = 4.2:1  ⚠️ FAILS for body text
   */
  ```

  **Step 2: Fix `--text-secondary` for card surfaces:**
  ```css
  /* Fix: Lighten secondary text on dark surfaces */
  --text-secondary: #999;  /* Bumps to 5.3:1 on #141414 — passes AA */
  
  /* Or use different value on cards: */
  .card { --text-secondary: #aaa; }  /* 6.3:1 on #141414 */
  ```

  **Tools:** Use [webaim.org/resources/contrastchecker](https://webaim.org/resources/contrastchecker/) or `npx @axe-core/cli http://localhost:7860`.

  **Acceptance:** Every text element passes AA contrast.

---

- [x] **3.2 — Keyboard Navigation**

  **Step 1: Add `tabindex` to all interactive elements that aren't natively focusable:**
  ```html
  <!-- Tab switchers need tabindex: -->
  <div class="tab" tabindex="0" role="tab" onclick="switchTab('voicelab')"
       onkeydown="if(event.key==='Enter')switchTab('voicelab')">VOICE LAB</div>
  
  <!-- Custom sliders need tabindex: -->
  <input type="range" id="ducking-range" tabindex="0" aria-label="Ducking Level">
  ```

  **Step 2: Add `:focus-visible` styles in `style.css`:**
  ```css
  /* Focus ring for keyboard users (not mouse clicks) */
  :focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: 2px;
  }
  
  /* Remove default outline for mouse users */
  :focus:not(:focus-visible) {
      outline: none;
  }
  
  /* Buttons and tabs */
  .btn:focus-visible,
  .tab:focus-visible {
      box-shadow: 0 0 0 3px rgba(204, 255, 0, 0.3);
  }
  ```

  **Step 3: Keyboard event handlers for custom components:**
  ```javascript
  // Tab key cycles through tabs:
  document.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              tab.click();
          }
      });
  });
  ```

  **Acceptance:** Tab through entire UI → all controls reachable. Enter activates buttons.

---

- [x] **3.3 — ARIA Labels & Landmarks**

  **Step 1: Add landmark regions to `index.html`:**
  ```html
  <nav id="main-nav" aria-label="Main Navigation">
      <!-- Tab bar -->
  </nav>
  <main id="main-content" aria-label="Content Area">
      <!-- Tab panels -->
  </main>
  <aside id="sidebar" aria-label="Task Manager">
      <!-- Task sidebar -->
  </aside>
  ```

  **Step 2: Add ARIA attributes to interactive elements:**
  ```html
  <!-- Audio player -->
  <audio id="main-audio-player" aria-label="Generated audio playback" controls></audio>
  
  <!-- Voice preview button -->
  <button id="preview-btn" aria-label="Preview selected voice">PREVIEW</button>
  
  <!-- Script editor -->
  <textarea id="script-editor" aria-label="Podcast script editor"
            aria-describedby="script-help"></textarea>
  <span id="script-help" class="sr-only">Enter your script using [Speaker] format</span>
  
  <!-- Tab panels -->
  <div id="voicelab-panel" role="tabpanel" aria-labelledby="voicelab-tab">...</div>
  
  <!-- Sliders -->
  <input type="range" aria-label="Pan control" aria-valuemin="-100" aria-valuemax="100">
  ```

  **Step 3: Add screen-reader-only utility class:**
  ```css
  .sr-only {
      position: absolute;
      width: 1px; height: 1px;
      padding: 0; margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border-width: 0;
  }
  ```

  **Acceptance:** Screen reader (NVDA/VoiceOver) navigates all sections and announces purposes.

---

- [ ] **3.4 — Reduced Motion Support**

  ```css
  /* Add at end of style.css: */
  @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
          scroll-behavior: auto !important;
      }
      
      /* Disable specific effects */
      .glow-effect { text-shadow: none !important; }
      .pulse-animation { animation: none !important; }
      .hover-lift:hover { transform: none !important; }
  }
  ```

  **Acceptance:** Enable "Reduce motion" in OS settings → all animations stop.

---

- [ ] **3.5 — High Contrast Mode**

  **Step 1: Define high-contrast theme variables:**
  ```css
  [data-theme="high-contrast"] {
      --bg: #000000;
      --surface: #0a0a0a;
      --accent: #ffffff;
      --text-primary: #ffffff;
      --text-secondary: #cccccc;
      --border: #ffffff;
  }
  
  [data-theme="high-contrast"] .card {
      border: 1px solid #ffffff;
      background: #000000;
  }
  
  [data-theme="high-contrast"] .btn {
      border: 2px solid #ffffff;
      color: #ffffff;
  }
  ```

  **Step 2: Add toggle button:**
  ```html
  <button id="contrast-toggle" onclick="toggleHighContrast()" aria-label="Toggle high contrast mode">
      <i class="fas fa-adjust"></i>
  </button>
  ```

  ```javascript
  function toggleHighContrast() {
      const current = document.documentElement.dataset.theme;
      const next = current === 'high-contrast' ? '' : 'high-contrast';
      document.documentElement.dataset.theme = next;
      localStorage.setItem('theme', next);
  }
  // Restore on load:
  document.documentElement.dataset.theme = localStorage.getItem('theme') || '';
  ```

  **Acceptance:** Toggle → all text white on black. All borders visible. No gradients.

---

## Key Files Reference

| File | Purpose | Key Lines |
|------|---------|-----------|
| `src/backend/api/system.py` | `/api/system/languages` endpoint | [NEW] L143+ |
| `src/backend/qwen_tts/inference/qwen3_tts_model.py` | `get_supported_languages()`, `_supported_languages_set()` | Language enumeration |
| `src/static/i18n.js` | [NEW] i18n loading system | `I18n.load()`, `I18n.t()`, `I18n.apply()` |
| `src/static/translations/en.json` | [NEW] English UI strings | All translatable text |
| `src/static/translations/zh.json` | [NEW] Chinese UI strings | Full Chinese translation |
| `src/static/shared.js` | `loadLanguages()`, `populateLanguageDropdown()` | [MODIFY] Dynamic language loading |
| `src/static/style.css` | `:focus-visible`, `.sr-only`, `@media reduced-motion`, high contrast theme | [MODIFY] Accessibility CSS |
| `src/static/index.html` | `data-i18n` attributes, ARIA labels, landmark regions, lang switcher | [MODIFY] All UI elements |

