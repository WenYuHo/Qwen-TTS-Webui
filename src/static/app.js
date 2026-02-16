// --- State & Storage ---
const SpeakerStore = {
    getVoices() {
        return JSON.parse(localStorage.getItem('qwen_voices') || '[]');
    },
    saveVoice(voice) {
        const voices = this.getVoices();
        voices.push(voice);
        localStorage.setItem('qwen_voices', JSON.stringify(voices));
        renderSpeakers();
    },
    deleteVoice(id) {
        const voices = this.getVoices().filter(v => v.id !== id);
        localStorage.setItem('qwen_voices', JSON.stringify(voices));
        renderSpeakers();
    },
    export() {
        const data = JSON.stringify(this.getVoices(), null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `qwen_voices_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
    },
    import(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const voices = JSON.parse(e.target.result);
                if (Array.isArray(voices)) {
                    localStorage.setItem('qwen_voices', JSON.stringify(voices));
                    renderSpeakers();
                    alert("Library imported successfully!");
                }
            } catch (err) { alert("Invalid library file"); }
        };
        reader.readAsText(file);
    }
};

const CanvasManager = {
    blocks: [],
    addBlock(role, text) {
        const id = Date.now().toString() + Math.random().toString(36).substr(2, 5);
        this.blocks.push({ id, role, text, status: 'idle', audioUrl: null });
    },
    moveBlock(id, direction) {
        const index = this.blocks.findIndex(b => b.id === id);
        if (index < 0) return;
        const newIndex = index + direction;
        if (newIndex < 0 || newIndex >= this.blocks.length) return;

        const temp = this.blocks[index];
        this.blocks[index] = this.blocks[newIndex];
        this.blocks[newIndex] = temp;
        renderBlocks();
    },
    deleteBlock(id) {
        this.blocks = this.blocks.filter(b => b.id !== id);
        renderBlocks();
    },
    clear() {
        this.blocks = [];
        this.save();
    },
    save() {
        // We don't save audioUrls as they are temporary Blobs
        const toSave = this.blocks.map(b => ({ role: b.role, text: b.text, status: b.status === 'ready' ? 'ready' : 'idle' }));
        localStorage.setItem('qwen_blocks', JSON.stringify(toSave));
    },
    load() {
        const saved = localStorage.getItem('qwen_blocks');
        if (saved) {
            this.blocks = JSON.parse(saved).map(b => ({ ...b, id: Math.random().toString(36).substr(2, 9), audioUrl: null }));
        }
    }
};

const PRESETS = ["Ryan", "Aiden", "Serena", "Anna", "Tess", "Ono_anna", "Melt", "Yuzu"];

// --- DOM Elements ---
const speakersList = document.getElementById('speakers-list');
const scriptEditor = document.getElementById('script-editor');
const statusMsg = document.getElementById('status-msg');
const audioPlayer = document.getElementById('audio-player');
const voiceModal = document.getElementById('voice-modal');
const blocksContainer = document.getElementById('blocks-container');

// --- View Management ---
function toggleView(view) {
    document.getElementById('draft-view').style.display = view === 'draft' ? 'block' : 'none';
    document.getElementById('prod-view').style.display = view === 'prod' ? 'block' : 'none';
}

function promoteToProduction() {
    const text = scriptEditor.value;
    const script = parseScript(text);

    if (script.length === 0) return alert("Write something in Draft mode first!");

    if (CanvasManager.blocks.length > 0 && !confirm("This will replace your existing Production timeline. Continue?")) return;

    CanvasManager.clear();
    script.forEach(line => CanvasManager.addBlock(line.role, line.text));
    CanvasManager.save();

    renderBlocks();
    toggleView('prod');
    statusMsg.innerText = "Production timeline ready";
}

async function batchSynthesize() {
    const idleBlocks = CanvasManager.blocks.filter(b => b.status === 'idle');
    if (idleBlocks.length === 0) return alert("No idle blocks to synthesize.");

    statusMsg.innerText = `Batch synthesizing ${idleBlocks.length} segments...`;
    for (const block of idleBlocks) {
        await generateBlock(block.id);
    }
    statusMsg.innerText = "Batch synthesis complete!";
}

// --- Speaker UI ---
function renderSpeakers() {
    speakersList.innerHTML = '';

    const presetH = document.createElement('h3');
    presetH.innerText = 'Templates';
    presetH.style.margin = '10px 0';
    speakersList.appendChild(presetH);

    PRESETS.forEach(name => {
        const div = createSpeakerItem(name, 'preset', name);
        speakersList.appendChild(div);
    });

    const customH = document.createElement('h3');
    customH.innerText = 'My Voices';
    customH.style.margin = '20px 0 10px 0';
    speakersList.appendChild(customH);

    const customVoices = SpeakerStore.getVoices();
    customVoices.forEach(v => {
        const div = createSpeakerItem(v.name, v.type, v.value, v.id);
        speakersList.appendChild(div);
    });

    // 3. Library Actions
    const actions = document.createElement('div');
    actions.style.display = 'flex';
    actions.style.gap = '8px';
    actions.style.marginTop = '12px';
    actions.innerHTML = `
        <button class="btn btn-secondary btn-sm" style="flex:1" onclick="SpeakerStore.export()">Export</button>
        <button class="btn btn-secondary btn-sm" style="flex:1" onclick="document.getElementById('import-file').click()">Import</button>
        <input type="file" id="import-file" style="display:none" onchange="SpeakerStore.import(this.files[0])">
    `;
    speakersList.appendChild(actions);
}

function createSpeakerItem(name, type, value, id = null) {
    const div = document.createElement('div');
    div.className = 'speaker-card';
    div.innerHTML = `
        <span class="speaker-role">${name}</span>
        <span style="font-size: 0.75rem; color: var(--text-secondary)">${type}</span>
        ${id ? `<button onclick="SpeakerStore.deleteVoice('${id}')" style="background:none; border:none; color:#a12; cursor:pointer; float:right;">×</button>` : ''}
    `;
    return div;
}

// --- Block UI ---
function renderBlocks() {
    blocksContainer.innerHTML = '';
    if (CanvasManager.blocks.length === 0) {
        blocksContainer.innerHTML = '<div class="empty-state"><p>No blocks. Write in Draft then Promote.</p></div>';
        return;
    }

    CanvasManager.blocks.forEach((block, idx) => {
        const div = document.createElement('div');
        div.className = 'story-block';
        div.innerHTML = `
            <div class="story-block-header">
                <div>
                    <span class="story-block-role">${block.role}</span>
                    <span class="status-indicator status-${block.status}">${block.status}</span>
                </div>
                <div>
                    <button class="btn btn-secondary btn-sm" onclick="CanvasManager.moveBlock('${block.id}', -1)" ${idx === 0 ? 'disabled' : ''}>↑</button>
                    <button class="btn btn-secondary btn-sm" onclick="CanvasManager.moveBlock('${block.id}', 1)" ${idx === CanvasManager.blocks.length - 1 ? 'disabled' : ''}>↓</button>
                    <button class="btn btn-secondary btn-sm btn-danger" onclick="CanvasManager.deleteBlock('${block.id}')">×</button>
                </div>
            </div>
            <div class="story-block-text">${block.text}</div>
            ${block.status === 'ready' ? '<div class="waveform-placeholder"></div>' : ''}
            <div class="story-block-actions">
                <button class="btn btn-secondary btn-sm" onclick="generateBlock('${block.id}')">
                    ${block.status === 'ready' ? 'Regenerate' : 'Synthesize'}
                </button>
                ${block.audioUrl ? `<button class="btn btn-primary btn-sm" onclick="playBlock('${block.id}')">▶ Play</button>` : ''}
            </div>
        `;
        blocksContainer.appendChild(div);
    });
}

async function generateBlock(id) {
    const block = CanvasManager.blocks.find(b => b.id === id);
    if (!block) return;

    block.status = 'generating';
    renderBlocks();

    const profiles = getAllProfiles();
    const script = [{ role: block.role, text: block.text }];

    try {
        const res = await fetch('/api/generate/segment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profiles, script })
        });

        if (!res.ok) throw new Error("Synthesis failed");

        const blob = await res.blob();
        block.audioUrl = URL.createObjectURL(blob);
        block.status = 'ready';
    } catch (e) {
        block.status = 'idle';
        alert("Error: " + e.message);
    } finally {
        renderBlocks();
    }
}

function playBlock(id) {
    const block = CanvasManager.blocks.find(b => b.id === id);
    if (block && block.audioUrl) {
        audioPlayer.src = block.audioUrl;
        audioPlayer.play();
    }
}

// --- Voice Studio ---
function addSpeaker() {
    openModal("Create New Voice", `
        <div class="control-group">
            <span class="label">Voice Name</span>
            <input type="text" id="new-voice-name" class="btn btn-secondary" placeholder="e.g. Grumpy Pirate" style="text-align:left; width:100%; margin-bottom:10px;">
        </div>
        <div class="control-group">
            <span class="label">Method</span>
            <select id="new-voice-type" class="btn btn-secondary" onchange="toggleVoiceFields()" style="text-align:left; width:100%; margin-bottom:10px;">
                <option value="design">Voice Design (Description)</option>
                <option value="clone">Clone from Audio (3s clip)</option>
            </select>
        </div>
        <div id="design-fields" class="control-group">
            <span class="label">Description</span>
            <textarea id="new-voice-desc" class="btn btn-secondary" style="height:60px; text-align:left; width:100%;" placeholder="A deep, rasping male voice..."></textarea>
        </div>
        <div id="clone-fields" class="control-group" style="display:none;">
            <span class="label">Audio File</span>
            <input type="file" id="new-voice-file" class="btn btn-secondary" style="width:100%;">
        </div>
    `, async () => {
        const name = document.getElementById('new-voice-name').value;
        const type = document.getElementById('new-voice-type').value;
        let value = "";

        if (type === 'design') {
            value = document.getElementById('new-voice-desc').value;
        } else {
            const fileInput = document.getElementById('new-voice-file');
            const file = fileInput.files[0];
            if (!file) return alert("Please select a file");

            statusMsg.innerText = "Uploading voice sample...";
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch('/api/voice/upload', { method: 'POST', body: formData });
            const data = await res.json();
            value = data.filename;
        }

        if (name && value) {
            SpeakerStore.saveVoice({ id: Date.now().toString(), name, type, value });
            closeModal();
            statusMsg.innerText = "Voice saved!";
        }
    });
}

function toggleVoiceFields() {
    const type = document.getElementById('new-voice-type').value;
    document.getElementById('design-fields').style.display = type === 'design' ? 'block' : 'none';
    document.getElementById('clone-fields').style.display = type === 'clone' ? 'block' : 'none';
}

// --- Modal Helper ---
function openModal(title, content, onSave) {
    document.getElementById('modal-title').innerText = title;
    document.getElementById('modal-content').innerHTML = content;
    document.getElementById('modal-save').onclick = onSave;
    voiceModal.style.display = 'flex';
}

function closeModal() {
    voiceModal.style.display = 'none';
}

// --- Script Logic ---
async function generatePodcast() {
    const inProd = document.getElementById('prod-view').style.display === 'block';

    let script = [];
    if (inProd) {
        script = CanvasManager.blocks.map(b => ({ role: b.role, text: b.text }));
    } else {
        const text = scriptEditor.value;
        script = parseScript(text);
    }

    const profiles = getAllProfiles();
    const bgm_mood = document.getElementById('bgm-select').value;

    if (script.length === 0) return alert("Please enter a script.");

    statusMsg.innerText = "Producing final podcast...";
    const btn = document.getElementById('generate-btn');
    btn.disabled = true;

    try {
        const response = await fetch('/api/generate/podcast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profiles, script, bgm_mood })
        });

        await handleAudioResponse(response);
        statusMsg.innerText = "Podcast ready! 🎉";
    } catch (e) {
        alert("Error: " + e.message);
        statusMsg.innerText = "Error in production";
    } finally {
        btn.disabled = false;
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
            script.push({ role: currentRole, text: currentText.join('\n').trim() });
        }
        currentText = [];
    };

    const roleRegex = /^\[(.+?)\]:(.*)/;
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

async function handleAudioResponse(response) {
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Generation failed");
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    audioPlayer.src = url;
    audioPlayer.play();
}

// --- Persistence ---
function autosave() {
    localStorage.setItem('qwen_draft', scriptEditor.value);
}

function loadAutosave() {
    const draft = localStorage.getItem('qwen_draft');
    if (draft) scriptEditor.value = draft;
}

// --- Init ---
renderSpeakers();
loadAutosave();
CanvasManager.load();
renderBlocks();
scriptEditor.addEventListener('input', autosave);

window.addSpeaker = addSpeaker;
window.generatePodcast = generatePodcast;
window.promoteToProduction = promoteToProduction;
window.batchSynthesize = batchSynthesize;
window.toggleView = toggleView;
window.generateBlock = generateBlock;
window.playBlock = playBlock;
window.toggleVoiceFields = toggleVoiceFields;
window.closeModal = closeModal;
window.SpeakerStore = SpeakerStore;
window.CanvasManager = CanvasManager;
