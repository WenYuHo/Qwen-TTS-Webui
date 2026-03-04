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
    addBlock(role, text) {
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
    },
    moveBlock(id, direction) {
        const index = this.blocks.findIndex(b => b.id === id);
        if (index < 0) return;
        const newIndex = index + direction;
        if (newIndex < 0 || newIndex >= this.blocks.length) return;

        const temp = this.blocks[index];
        this.blocks[index] = this.blocks[newIndex];
        this.blocks[newIndex] = temp;
    },
    deleteBlock(id) {
        this.blocks = this.blocks.filter(b => b.id !== id);
    },
    updateBlock(id, updates) {
        const block = this.blocks.find(b => b.id === id);
        if (block) Object.assign(block, updates);
    },
    clear() {
        this.blocks = [];
    },
    save() {
        const toSave = this.blocks.map(b => ({
            role: b.role,
            text: b.text,
            status: b.status === 'ready' ? 'ready' : 'idle',
            language: b.language,
            pause_after: b.pause_after
        }));
        localStorage.setItem('qwen_blocks', JSON.stringify(toSave));
    },
    load() {
        const saved = localStorage.getItem('qwen_blocks');
        if (saved) {
            this.blocks = JSON.parse(saved).map(b => ({ ...b, id: Math.random().toString(36).substr(2, 9), audioUrl: null }));
        }
    }
};

const previewCache = new Map();

async function getVoicePreview(profile) {
    // Cache key based on profile values (type and value/instruct)
    const cacheKey = `${profile.type}:${profile.value}`;
    if (previewCache.has(cacheKey)) {
        console.log(`[BOLT] Using cached preview for ${profile.role}`);
        return previewCache.get(cacheKey);
    }

    try {
        const res = await fetch('/api/voice/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profile)
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
            
            // ⚡ Bolt: Split text by [instruct] or (non-verbal-tag)
            // Allows mid-sentence emotional shifts or cues.
            const splitRegex = /(\[.+?\]|\(.+?\))/g;
            const parts = rawText.split(splitRegex);
            
            let activeInstruct = null;
            
            parts.forEach((part, index) => {
                if (!part) return;
                
                const instructMatch = part.match(/^\[(.+?)\]$/) || part.match(/^\((.+?)\)$/);
                if (instructMatch) {
                    activeInstruct = instructMatch[1];
                    
                    // ⚡ Bolt: If tag is at the end or followed by another tag, synthesize it as text
                    const nextPart = parts[index + 1];
                    const followedByInstruct = nextPart && (nextPart.match(/^\[(.+?)\]$/) || nextPart.match(/^\((.+?)\)$/));
                    
                    if (!nextPart || followedByInstruct) {
                        script.push({
                            role: currentRole,
                            text: `(${activeInstruct})`,
                            instruct: activeInstruct,
                            language: 'auto',
                            pause_after: 0.3
                        });
                    }
                } else {
                    const cleanPart = part.trim();
                    if (cleanPart) {
                        script.push({ 
                            role: currentRole, 
                            text: cleanPart,
                            instruct: activeInstruct,
                            language: 'auto',
                            pause_after: 0.2 
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
