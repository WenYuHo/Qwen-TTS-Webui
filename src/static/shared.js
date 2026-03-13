// --- Shared State & Logic for Qwen-TTS Studio ---

function escapeHTML(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

async function loadLanguages() {
    if (window._languages) return window._languages;
    try {
        const res = await fetch('/api/system/languages');
        const data = await res.json();
        window._languages = data;
        return data;
    } catch (e) {
        console.error("Failed to load languages:", e);
        return { languages: [{ code: 'en', name: 'English' }], dialects: {} };
    }
}

function populateLanguageDropdown(selectId, includeAuto = true) {
    const select = document.getElementById(selectId);
    if (!select || !window._languages) return;
    
    const currentValue = select.value;
    select.innerHTML = '';
    if (includeAuto) {
        const opt = document.createElement('option');
        opt.value = 'auto';
        opt.textContent = 'Auto Detect';
        select.appendChild(opt);
    }
    
    window._languages.languages.forEach(lang => {
        const opt = document.createElement('option');
        opt.value = lang.code;
        opt.textContent = lang.name;
        select.appendChild(opt);
    });
    
    if (currentValue) select.value = currentValue;
}

const SpeakerStore = {
    getVoices() {
        return JSON.parse(localStorage.getItem('qwen_voices') || '[]');
    },
    saveVoice(voice) {
        const voices = this.getVoices();
        voices.push(voice);
        localStorage.setItem('qwen_voices', JSON.stringify(voices));
    },
    deleteVoice(id) {
        const voices = this.getVoices().filter(v => v.id !== id);
        localStorage.setItem('qwen_voices', JSON.stringify(voices));
    }
};

const CanvasManager = {
    blocks: [],
    _undoStack: [],
    _redoStack: [],
    _maxHistory: 50,

    _saveSnapshot() {
        this._undoStack.push(JSON.parse(JSON.stringify(this.blocks)));
        if (this._undoStack.length > this._maxHistory) this._undoStack.shift();
        this._redoStack = []; // Clear redo on new action
    },

    undo() {
        if (this._undoStack.length === 0) return;
        this._redoStack.push(JSON.parse(JSON.stringify(this.blocks)));
        this.blocks = this._undoStack.pop();
        window.ProductionManager?.renderBlocks();
        this.save();
    },

    redo() {
        if (this._redoStack.length === 0) return;
        this._undoStack.push(JSON.parse(JSON.stringify(this.blocks)));
        this.blocks = this._redoStack.pop();
        window.ProductionManager?.renderBlocks();
        this.save();
    },

    addBlock(role, text) {
        this._saveSnapshot();
        const id = Date.now().toString() + Math.random().toString(36).substr(2, 5);
        this.blocks.push({
            id,
            role,
            text,
            status: 'idle',
            audioUrl: null,
            startTime: 0,
            duration: 0,
            language: 'auto',
            pause_after: 0.5
        });
        this.save();
    },
    moveBlock(id, direction) {
        this._saveSnapshot();
        const index = this.blocks.findIndex(b => b.id === id);
        if (index < 0) return;
        const newIndex = index + direction;
        if (newIndex < 0 || newIndex >= this.blocks.length) return;

        const temp = this.blocks[index];
        this.blocks[index] = this.blocks[newIndex];
        this.blocks[newIndex] = temp;
        this.save();
    },
    deleteBlock(id) {
        this._saveSnapshot();
        this.blocks = this.blocks.filter(b => b.id !== id);
        this.save();
    },
    updateBlock(id, updates) {
        this._saveSnapshot();
        const block = this.blocks.find(b => b.id === id);
        if (block) Object.assign(block, updates);
        this.save();
    },
    clear() {
        this._saveSnapshot();
        this.blocks = [];
        this.save();
    },
    save() {
        const toSave = this.blocks.map(b => ({
            id: b.id,
            role: b.role,
            text: b.text,
            status: b.status === 'ready' ? 'ready' : 'idle',
            language: b.language,
            pause_after: b.pause_after,
            pan: b.pan,
            temperature: b.temperature
        }));
        localStorage.setItem('qwen_blocks', JSON.stringify(toSave));
    },
    load() {
        const saved = localStorage.getItem('qwen_blocks');
        if (saved) {
            this.blocks = JSON.parse(saved).map(b => ({ ...b, audioUrl: null }));
        }
    }
};

const previewCache = new Map();

async function getVoicePreview(profile) {
    // Cache key based on profile values (type and value/instruct)
    const customText = document.getElementById('custom-preview-text')?.value?.trim() || '';
    const cacheKey = `${profile.type}:${profile.value}:${customText}`;
    if (previewCache.has(cacheKey)) {
        console.log(`[BOLT] Using cached preview for ${profile.role}`);
        return previewCache.get(cacheKey);
    }

    try {
        const body = { ...profile };
        if (customText) body.preview_text = customText;
        const res = await fetch('/api/voice/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!res.ok) throw new Error("Preview failed");
        const blob = await res.blob();
        previewCache.set(cacheKey, blob);
        return blob;
    } catch (e) {
        console.error("Preview error:", e);
        return null;
    }
}

const TaskPoller = {
    async poll(taskId, onProgress, interval = 1000) {
        return new Promise((resolve, reject) => {
            const timer = setInterval(async () => {
                try {
                    const res = await fetch(`/api/tasks/${taskId}`);
                    if (!res.ok) throw new Error("Status check failed");

                    const task = await res.json();
                    if (onProgress) onProgress(task);

                    if (task.status === 'completed') {
                        clearInterval(timer);
                        const resultRes = await fetch(`/api/tasks/${taskId}/result`);
                        if (!resultRes.ok) throw new Error("Failed to download result");
                        const blob = await resultRes.blob();
                        resolve(blob);
                    } else if (task.status === 'failed') {
                        clearInterval(timer);
                        reject(new Error(task.error || "Task failed"));
                    }
                } catch (e) {
                    clearInterval(timer);
                    reject(e);
                }
            }, interval);
        });
    }
};

const UIHeartbeat = {
    start() {
        const dot = document.getElementById('heartbeat-dot');
        if (!dot) return;

        setInterval(() => {
            dot.style.opacity = '1';
            setTimeout(() => {
                dot.style.opacity = '0.3';
            }, 100);
        }, 2000);
    }
};

let PRESETS = [];

async function initializePresets() {
    try {
        const res = await fetch('/api/voice/speakers');
        const data = await res.json();
        PRESETS = data.presets || [];
    } catch (e) {
        console.error("Failed to fetch presets:", e);
        // Fallback to minimal set if backend fails
        PRESETS = ["aiden", "dylan", "eric", "ono_anna", "ryan", "serena", "sohee", "uncle_fu", "vivian"];
    }
}

function getAllProfiles() {
    const profiles = [];
    PRESETS.forEach(p => profiles.push({ role: p, type: 'preset', value: p }));
    SpeakerStore.getVoices().forEach(v => profiles.push({ role: v.name, type: v.type, value: v.value }));
    return profiles;
}

function parseScript(text) {
    const lines = text.split('\n');
    const script = [];
    let currentRole = null;
    let currentText = [];

    const flush = () => {
        if (currentRole && currentText.length > 0) {
            const rawText = currentText.join('\n').trim();

            // ⚡ Bolt: Split text by [instruct] or (non-verbal-tag) or <pause:Xs>
            // Allows mid-sentence emotional shifts, cues, or pauses.
            const splitRegex = /(\[.+?\]|\(.+?\)|<pause:[\d.]+s?>)/gi;
            const parts = rawText.split(splitRegex);

            let activeInstruct = null;

            parts.forEach((part, index) => {
                if (!part) return;

                const instructMatch = part.match(/^\[(.+?)\]$/) || part.match(/^\((.+?)\)$/);
                const pauseMatch = part.match(/<pause:([\d.]+)s?>/i);

                if (instructMatch) {
                    activeInstruct = instructMatch[1];

                    // ⚡ Bolt: If tag is at the end or followed by another tag/pause, synthesize it as text
                    const nextPart = parts[index + 1];
                    const followedBySpecial = nextPart && (
                        nextPart.match(/^\[(.+?)\]$/) || 
                        nextPart.match(/^\((.+?)\)$/) || 
                        nextPart.match(/<pause:[\d.]+s?>/i)
                    );

                    if (!nextPart || followedBySpecial) {
                        script.push({
                            role: currentRole,
                            text: `(${activeInstruct})`,
                            instruct: activeInstruct,
                            language: 'auto',
                            pause_after: 0.3
                        });
                    }
                } else if (pauseMatch) {
                    const duration = parseFloat(pauseMatch[1]);
                    if (script.length > 0) {
                        // Attach pause to the previous segment
                        script[script.length - 1].pause_after = duration;
                    } else {
                        // If it's at the very beginning, add a tiny silent segment
                        script.push({
                            role: currentRole,
                            text: " ",
                            instruct: "silence",
                            language: 'auto',
                            pause_after: duration
                        });
                    }
                } else {
                    let cleanPart = part.trim();
                    if (cleanPart) {
                        // Handle "..." as a 1.0s pause
                        let pauseAfter = 0.2;
                        if (cleanPart.endsWith('...')) {
                            pauseAfter = 1.0;
                        }

                        // Extract emphasis markers *word* or **word**
                        const emphasized = [];
                        cleanPart = cleanPart.replace(/\*\*(.+?)\*\*/g, (_, word) => { emphasized.push(word); return word; });
                        cleanPart = cleanPart.replace(/\*(.+?)\*/g, (_, word) => { emphasized.push(word); return word; });

                        let lineInstruct = activeInstruct;
                        if (emphasized.length > 0) {
                            lineInstruct = (lineInstruct ? lineInstruct + ", " : "") + `emphasize the words: "${emphasized.join('", "')}"`;
                        }

                        script.push({
                            role: currentRole,
                            text: cleanPart,
                            instruct: lineInstruct,
                            language: 'auto',
                            pause_after: pauseAfter
                        });
                    }
                }
            });
        }
        currentText = [];
    };

    // Support both "Alice: ..." and "[Alice]: ..."
    const roleRegex = /^(?:\[)?([^\]:]+)(?:\])?\s*:\s*(.*)/;
    lines.forEach(line => {
        const match = line.match(roleRegex);
        if (match) {
            flush();
            currentRole = match[1].trim();
            if (match[2].trim()) currentText.push(match[2].trim());
        } else if (currentRole) {
            currentText.push(line);
        }
    });
    flush();
    return script;
}

// Global Exposure
Object.assign(window, {
    CanvasManager,
    parseScript,
    TaskPoller,
    UIHeartbeat,
    SpeakerStore,
    escapeHTML,
    getVoicePreview,
    getAllProfiles: async () => {
        const [libRes, speakerRes] = await Promise.all([
            fetch('/api/voice/library'),
            fetch('/api/voice/speakers')
        ]);
        const libData = await libRes.json();
        const speakerData = await speakerRes.json();

        const profiles = {};
        speakerData.presets.forEach(p => profiles[p] = { type: 'preset', value: p });
        libData.voices.forEach(v => profiles[v.name] = v.profile);
        return profiles;
    }
});
