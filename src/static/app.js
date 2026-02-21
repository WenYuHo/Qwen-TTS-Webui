// app.js - Main Dashboard Logic
// Dependence: shared.js
// All state logic (SpeakerStore, CanvasManager) is handled in shared.js

// --- UI Elements ---
const speakersList = document.getElementById('speakers-list');
const scriptEditor = document.getElementById('script-editor');
const statusMsg = document.getElementById('status-msg');
const audioPlayer = document.getElementById('audio-player');
const voiceModal = document.getElementById('voice-modal');
const blocksContainer = document.getElementById('blocks-container');

// --- Speaker Rendering ---
function renderSpeakers() {
    speakersList.innerHTML = '';

    // Presets
    PRESETS.forEach(p => {
        speakersList.appendChild(createSpeakerItem(p, 'preset', p));
    });

    // Custom Voices
    const customVoices = SpeakerStore.getVoices();
    if (customVoices.length > 0) {
        const divider = document.createElement('div');
        divider.className = 'label';
        divider.style.padding = '8px 16px';
        divider.innerText = 'My Voices';
        speakersList.appendChild(divider);

        customVoices.forEach(v => {
            speakersList.appendChild(createSpeakerItem(v.name, v.type, v.value, v.id));
        });
    }

    // Actions
    const actions = document.createElement('div');
    actions.style.display = 'flex';
    actions.style.gap = '8px';
    actions.style.marginTop = '12px';
    actions.innerHTML = `
        <button class="btn btn-secondary btn-sm" style="flex:1" onclick="exportVoices()">Export</button>
        <button class="btn btn-secondary btn-sm" style="flex:1" onclick="document.getElementById('import-file').click()">Import</button>
        <input type="file" id="import-file" style="display:none" onchange="importVoices(this.files[0])">
    `;
    speakersList.appendChild(actions);
}

function createSpeakerItem(name, type, value, id = null) {
    const div = document.createElement('div');
    div.className = 'speaker-card';
    div.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; width:100%">
            <div style="flex:1">
                <span class="speaker-role">${name}</span>
                <span style="font-size: 0.65rem; color: var(--text-secondary); display:block">${type}</span>
            </div>
            <div style="display:flex; gap:4px; align-items:center;">
                <button class="btn btn-secondary btn-sm" style="padding: 2px 6px; font-size: 0.7rem;" onclick="playVoicePreview('${name}', '${type}', '${value}')">🔊</button>
                ${id ? `<button onclick="deleteVoice('${id}')" style="background:none; border:none; color:#a12; cursor:pointer; font-size:1.2rem;">×</button>` : ''}
            </div>
        </div>
    `;
    return div;
}

// --- Voice Preview ---
async function playVoicePreview(role, type, value) {
    statusMsg.innerText = `Previewing ${role}...`;
    const blob = await getVoicePreview({ role, type, value });
    if (blob) {
        const url = URL.createObjectURL(blob);
        const previewPlayer = new Audio(url);
        previewPlayer.play();
        statusMsg.innerText = "Ready";
    } else {
        statusMsg.innerText = "Preview failed.";
    }
}

// --- Library Actions (Wrappers) ---
function deleteVoice(id) {
    if (confirm("Delete this voice?")) {
        SpeakerStore.deleteVoice(id);
        renderSpeakers();
    }
}

function exportVoices() {
    const data = JSON.stringify(SpeakerStore.getVoices(), null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `qwen_voices_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
}

function importVoices(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const voices = JSON.parse(e.target.result);
            if (Array.isArray(voices)) {
                localStorage.setItem('qwen_voices', JSON.stringify(voices));
                renderSpeakers();
                alert("Library imported!");
            }
        } catch (err) { alert("Invalid library file"); }
    };
    reader.readAsText(file);
}

// --- View Management ---
function toggleView(view) {
    document.getElementById('draft-view').style.display = view === 'draft' ? 'block' : 'none';
    document.getElementById('prod-view').style.display = view === 'prod' ? 'block' : 'none';

    if (view === 'prod' && window.TimelineManager) {
        setTimeout(() => window.TimelineManager.renderTimeline(), 100);
    }
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
                    <button class="btn btn-secondary btn-sm" onclick="moveBlock('${block.id}', -1)" ${idx === 0 ? 'disabled' : ''}>↑</button>
                    <button class="btn btn-secondary btn-sm" onclick="moveBlock('${block.id}', 1)" ${idx === CanvasManager.blocks.length - 1 ? 'disabled' : ''}>↓</button>
                    <button class="btn btn-secondary btn-sm btn-danger" onclick="deleteBlock('${block.id}')">×</button>
                </div>
            </div>
            <div class="story-block-text">${block.text}</div>
            ${block.status === 'generating' ? `
                <div class="progress-container">
                    <div class="progress-bar" style="width: ${block.progress}%"></div>
                </div>
                <div style="font-size: 0.7rem; color: var(--text-secondary); margin-bottom: 8px;">${block.status_msg || 'Initializing...'}</div>
            ` : ''}
            ${block.status === 'ready' ? '<div class="waveform-placeholder"></div>' : ''}
            <div class="story-block-actions">
                <button class="btn btn-secondary btn-sm" onclick="generateBlock('${block.id}')">
                    ${block.status === 'ready' ? 'Regenerate' : (block.status === 'error' ? 'Retry' : 'Synthesize')}
                </button>
                ${block.audioUrl ? `<button class="btn btn-primary btn-sm" onclick="playBlock('${block.id}')">▶ Play</button>` : ''}
            </div>
        `;
        blocksContainer.appendChild(div);
    });
}

function moveBlock(id, dir) {
    CanvasManager.moveBlock(id, dir);
    CanvasManager.save();
    renderBlocks();
}

function deleteBlock(id) {
    CanvasManager.deleteBlock(id);
    CanvasManager.save();
    renderBlocks();
}

async function generateBlock(id) {
    const block = CanvasManager.blocks.find(b => b.id === id);
    if (!block) return;

    block.status = 'generating';
    block.progress = 0;
    renderBlocks();

    const profiles = getAllProfiles();
    const script = [{ role: block.role, text: block.text }];

    try {
        const res = await fetch('/api/generate/segment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profiles, script })
        });

        if (!res.ok) throw new Error("Synthesis initiation failed");
        const { task_id } = await res.json();

        // Start polling
        const blob = await TaskPoller.poll(task_id, (task) => {
            block.progress = task.progress;
            block.status_msg = task.message;
            renderBlocks();
        });

        block.audioUrl = URL.createObjectURL(blob);
        block.status = 'ready';
        block.progress = 100;

        // Get duration for timeline
        const tempAudio = new Audio(block.audioUrl);
        tempAudio.onloadedmetadata = () => {
            block.duration = tempAudio.duration;
            CanvasManager.save(); // Save duration
            if (window.TimelineManager) window.TimelineManager.renderTimeline();
        };

    } catch (e) {
        block.status = 'error';
        block.status_msg = e.message;
        console.error("Synthesis failed:", e);
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

// --- Production Logic ---
async function batchSynthesize() {
    const blocksToSynth = CanvasManager.blocks.filter(b => b.status !== 'ready');
    if (blocksToSynth.length === 0) return alert("All blocks are already synthesized!");

    document.getElementById('batch-btn').disabled = true;
    for (const block of blocksToSynth) {
        await generateBlock(block.id);
    }
    document.getElementById('batch-btn').disabled = false;
}

async function generatePodcast() {
    const inProd = document.getElementById('prod-view').style.display === 'block';
    let script = [];
    if (inProd) {
        script = CanvasManager.blocks.map(b => ({
            role: b.role,
            text: b.text,
            start_time: b.startTime // Ensure this is sent
        }));
    } else {
        script = parseScript(scriptEditor.value);
        // implicit timing for draft mode (null start_time will trigger sequential)
    }

    const profiles = getAllProfiles();
    const bgm_mood = document.getElementById('bgm-select').value;

    if (script.length === 0) return alert("Please enter a script.");

    statusMsg.innerText = "Initiating production...";
    const btn = document.getElementById('generate-btn');
    btn.disabled = true;

    try {
        const response = await fetch('/api/generate/podcast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profiles, script, bgm_mood })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Generation failed");
        }
        
        const { task_id } = await response.json();
        
        // Polling for podcast generation
        const blob = await TaskPoller.poll(task_id, (task) => {
            statusMsg.innerText = `Production: ${task.message} (${task.progress}%)`;
        });

        const url = URL.createObjectURL(blob);
        audioPlayer.src = url;
        audioPlayer.play();
        statusMsg.innerText = "Podcast ready! 🎉";
    } catch (e) {
        alert("Error: " + e.message);
        statusMsg.innerText = "Error in production";
    } finally {
        btn.disabled = false;
    }
}

// --- Utils ---
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
UIHeartbeat.start();
scriptEditor.addEventListener('input', autosave);

// Globals for HTML onclicks
window.toggleView = toggleView;
window.promoteToProduction = promoteToProduction;
window.generatePodcast = generatePodcast;
window.batchSynthesize = batchSynthesize;
window.generateBlock = generateBlock;
window.playBlock = playBlock;
window.moveBlock = moveBlock;
window.deleteBlock = deleteBlock;
window.playVoicePreview = playVoicePreview;
window.deleteVoice = deleteVoice;
window.importVoices = importVoices;
window.exportVoices = exportVoices;
window.saveProject = saveProject;
window.loadProject = loadProject;

// --- Project Management ---
async function fetchProjects() {
    const select = document.getElementById('project-select');
    select.innerHTML = '<option value="">(New Project)</option>';

    try {
        const res = await fetch('/api/projects');
        const data = await res.json();
        data.projects.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p;
            opt.innerText = p;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error("Failed to fetch projects", e);
    }
}

async function saveProject() {
    let name = document.getElementById('project-select').value;
    if (!name) {
        name = prompt("Enter project name:");
    }
    if (!name) return;

    const draftText = scriptEditor.value;
    const blocks = CanvasManager.blocks.map(b => ({
        id: b.id,
        role: b.role,
        text: b.text,
        status: b.status
    }));

    try {
        const res = await fetch(`/api/projects/${name}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                blocks: blocks,
                script_draft: draftText
            })
        });

        if (res.ok) {
            alert("Project saved!");
            fetchProjects(); // refresh list
            // Set select to this project
            setTimeout(() => document.getElementById('project-select').value = name, 500);
        } else {
            alert("Failed to save project.");
        }
    } catch (e) {
        alert("Error saving: " + e.message);
    }
}

async function loadProject() {
    const name = document.getElementById('project-select').value;
    if (!name) return alert("Select a project first.");

    if (CanvasManager.blocks.length > 0 && !confirm("Overwrite current workspace?")) return;

    try {
        const res = await fetch(`/api/projects/${name}`);
        if (!res.ok) throw new Error("Load failed");

        const data = await res.json();

        // Restore Draft
        scriptEditor.value = data.script_draft || "";
        localStorage.setItem('qwen_draft', scriptEditor.value);

        // Restore Blocks
        CanvasManager.clear();
        if (data.blocks && Array.isArray(data.blocks)) {
            data.blocks.forEach(b => {
                // Re-add block (manual push to preserve IDs if we wanted, but logic generates new IDs usually. 
                // Let's force push for now to keep state simple, or reuse addBlock logic).
                // Actually CanvasManager.addBlock generates ID. 
                // We should probably allow restoring explicit state.
                // Let's just push manually to blocks array for fidelity.
                CanvasManager.blocks.push({
                    id: b.id,
                    role: b.role,
                    text: b.text,
                    status: 'idle', // Reset status to force re-gen or idle? Or keep 'ready' if we had audio?
                    // Audio is not saved in JSON. So reset to idle/ready but no url.
                    // If 'ready', user might think it plays. But we don't have the blob URL anymore.
                    // So set to 'idle'.
                    audioUrl: null
                });
            });
        }
        CanvasManager.save();
        renderBlocks();
        alert("Project loaded!");

    } catch (e) {
        alert("Error loading: " + e.message);
    }
}

// Init additional
fetchProjects();

// For voice modal (addSpeaker, toggleVoiceFields, closeModal) - these functions are assumed to be in shared.js or handled differently now.
// The voiceModal element is still present, so its usage might be internal to shared.js or another module.
// For now, we'll assume the modal functions are not directly exposed globally from app.js anymore.
// If addSpeaker is still needed globally, it would need to be imported and exposed.
// For the purpose of this edit, only the explicitly mentioned global functions are exposed.
