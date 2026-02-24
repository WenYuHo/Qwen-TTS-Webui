import { TimelineManager } from './js/timeline.js';
import { TaskMonitor } from './js/tasks.js';
import { switchView, renderSpeechVoiceList, renderVoiceLibrary, renderBlocks } from './js/ui.js';
import { generateSpeech } from './js/voice_lab.js'; // Wait, I should move generateSpeech to voice_lab.js or tts.js
import {
    testVoiceDesign, playDesignPreview, saveDesignedVoice,
    handleCloneUpload, testVoiceClone, playClonePreview, saveClonedVoice,
    testVoiceMix, playMixPreview, saveMixedVoice,
    uploadVoiceImage, TimelineManager, deleteVoice,
    startDubbing, startVoiceChanger
} from './js/voice_lab.js';
import {
    fetchProjects, saveProject, loadProject, promoteToProduction,
    toggleCanvasView, generateBlock, playBlock, deleteBlock,
    generatePodcast, batchSynthesize, generateVideo, updateBlockProperty
} from './js/project.js';
import { renderSystemView, downloadModel } from './js/system.js';
import { state } from './js/state.js';

// --- Initialization ---

window.onload = () => {
    switchView('home');
    TaskMonitor.init('task-monitor-container');
    setupEventListeners();
    setInterval(() => {
        const dot = document.getElementById('heartbeat');
        if (dot) { dot.style.opacity = '1'; setTimeout(() => dot.style.opacity = '0.3', 200); }
    }, 2000);
};

function renderAvatar(name) {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#D4A5A5', '#9B59B6'];
    const color = colors[name.length % colors.length];
    return `<div class="avatar" style="background:${color}" title="${name}" aria-label="Avatar for ${name}">${name[0].toUpperCase()}</div>`;
}

function switchView(view) {
    state.currentView = view;
    document.querySelectorAll('.view-container').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(v => v.classList.remove('active'));

    document.getElementById(`${view}-view`).classList.add('active');
    document.querySelector(`button[onclick="switchView('${view}')"]`).classList.add('active');

    if (view === 'speech') {
        renderSpeechVoiceList();
        renderVoiceLibrary();
    }
    if (view === 'dubbing') {
        renderS2STargetList();
    }
    if (view === 'system') {
        renderSystemView();
    }
}

// --- Voice Studio ---

function renderSpeechVoiceList() {
    const selects = ['mix-voice-a', 'mix-voice-b'];
    const profiles = getAllProfiles();

    selects.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = '';
        profiles.forEach(p => {
            const opt = document.createElement('option');
            opt.value = JSON.stringify(p);
            opt.innerText = p.role;
            el.appendChild(opt);
        });
    });
}

function renderS2STargetList() {
    const el = document.getElementById('s2s-target-voice');
    if (!el) return;
    const profiles = getAllProfiles();
    el.innerHTML = '';
    profiles.forEach(p => {
        const opt = document.createElement('option');
        opt.value = JSON.stringify(p);
        opt.innerText = p.role;
        el.appendChild(opt);
    });
}

async function testVoiceDesign(btn) {
    if (btn) {
        btn.disabled = true;
        btn.setAttribute('aria-busy', 'true');
        btn.dataset.originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Designing...';
    }
    const prompt = document.getElementById('design-prompt').value;
    const gender = document.getElementById('design-gender').value;
    const age = document.getElementById('design-age').value;
    const instruct = `${prompt}. Gender: ${gender}, Age: ${age}`;

    const status = document.getElementById('design-status');
    const container = document.getElementById('design-preview-container');

    status.innerText = "Designing...";
    container.style.display = 'block';

    try {
        const blob = await getVoicePreview({ role: 'Designed Voice', type: 'design', value: instruct });
        const url = URL.createObjectURL(blob);
        state.voicelab.lastDesignedPath = instruct;
        window.designPreviewUrl = url;
        status.innerText = "Ready";
    } catch (e) {
        status.innerText = "Error: " + e.message;
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.removeAttribute('aria-busy');
            btn.innerHTML = btn.dataset.originalHtml;
        }
    }
}

function playDesignPreview() {
    if (window.designPreviewUrl) {
        const player = document.getElementById('preview-player');
        player.src = window.designPreviewUrl;
        player.play();
    }
}

function saveDesignedVoice() {
    const name = prompt("Voice Name:");
    if (!name || !state.voicelab.lastDesignedPath) return;
    SpeakerStore.saveVoice({ id: Date.now(), name, type: 'design', value: state.voicelab.lastDesignedPath });
    renderVoiceLibrary();
    renderSpeechVoiceList();
}

async function handleCloneUpload(files) {
    if (!files || files.length === 0) return;
    const filenames = [];
    for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('file', files[i]);
        const res = await fetch('/api/voice/upload', { method: 'POST', body: formData });
        const data = await res.json();
        filenames.push(data.filename);
    }
    state.voicelab.lastClonedPath = filenames.join('|');
    document.getElementById('clone-filename').innerText = files.length > 1 ? `${files.length} samples selected` : files[0].name;
}

async function testVoiceClone(btn) {
    if (!state.voicelab.lastClonedPath) return alert("Upload audio first");
    if (btn) {
        btn.disabled = true;
        btn.setAttribute('aria-busy', 'true');
        btn.dataset.originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cloning...';
    }
    const status = document.getElementById('clone-status');
    const container = document.getElementById('clone-preview-container');
    status.innerText = "Cloning...";
    container.style.display = 'block';

    try {
        const blob = await getVoicePreview({ role: 'Cloned Voice', type: 'clone', value: state.voicelab.lastClonedPath });
        window.clonePreviewUrl = URL.createObjectURL(blob);
        status.innerText = "Ready";
    } catch (e) { status.innerText = "Error"; }
    finally {
        if (btn) {
            btn.disabled = false;
            btn.removeAttribute('aria-busy');
            btn.innerHTML = btn.dataset.originalHtml;
        }
    }
}

function playClonePreview() {
    if (window.clonePreviewUrl) {
        const player = document.getElementById('preview-player');
        player.src = window.clonePreviewUrl;
        player.play();
    }
}

function saveClonedVoice() {
    const name = prompt("Voice Name:");
    if (!name || !state.voicelab.lastClonedPath) return;
    SpeakerStore.saveVoice({ id: Date.now(), name, type: 'clone', value: state.voicelab.lastClonedPath });
    renderVoiceLibrary();
    renderSpeechVoiceList();
}

async function testVoiceMix(btn) {
    if (btn) {
        btn.disabled = true;
        btn.setAttribute('aria-busy', 'true');
        btn.dataset.originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Mixing...';
    }
    const voiceA = JSON.parse(document.getElementById('mix-voice-a').value);
    const voiceB = JSON.parse(document.getElementById('mix-voice-b').value);
    const weightA = parseInt(document.getElementById('mix-weight-a').value) / 100;
    const weightB = parseInt(document.getElementById('mix-weight-b').value) / 100;

    const mixConfig = [
        { profile: voiceA, weight: weightA },
        { profile: voiceB, weight: weightB }
    ];

    const status = document.getElementById('mix-status');
    const container = document.getElementById('mix-preview-container');
    status.innerText = "Mixing...";
    container.style.display = 'block';

    try {
        const mixVal = JSON.stringify(mixConfig);
        const blob = await getVoicePreview({ role: 'Mixed Voice', type: 'mix', value: mixVal });
        window.mixPreviewUrl = URL.createObjectURL(blob);
        state.voicelab.lastMixedPath = mixVal;
        status.innerText = "Ready";
    } catch (e) { status.innerText = "Error"; }
    finally {
        if (btn) {
            btn.disabled = false;
            btn.removeAttribute('aria-busy');
            btn.innerHTML = btn.dataset.originalHtml;
        }
    }
}

function playMixPreview() {
    if (window.mixPreviewUrl) {
        const player = document.getElementById('preview-player');
        player.src = window.mixPreviewUrl;
        player.play();
    }
}

function saveMixedVoice() {
    const name = prompt("Voice Name:");
    if (!name || !state.voicelab.lastMixedPath) return;
    SpeakerStore.saveVoice({ id: Date.now(), name, type: 'mix', value: state.voicelab.lastMixedPath });
    renderVoiceLibrary();
    renderSpeechVoiceList();
}

function renderVoiceLibrary() {
    const grid = document.getElementById('voice-library-grid');
    if (!grid) return;
    grid.innerHTML = '';

    const voices = SpeakerStore.getVoices();
    if (voices.length === 0) {
        grid.innerHTML = `
            <div class="card" style="grid-column: 1 / -1; text-align: center; padding: 48px; background: rgba(255,255,255,0.02); border-style: dashed; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px;">
                <i class="fas fa-microphone-slash fa-3x" style="color: var(--text-secondary); opacity: 0.5;"></i>
                <p style="color: var(--text-secondary); max-width: 300px;">Your voice library is empty. Design or clone a voice to get started!</p>
            </div>
        `;
        return;
    }

    voices.forEach(v => {
        const div = document.createElement('div');
        div.className = 'card voice-card';
        div.innerHTML = `
            <div style="display:flex; align-items:center; gap:16px;">
                ${renderAvatar(v.name)}
                <div style="flex:1">
                    <h3 style="margin:0; font-size:1rem;">${v.name}</h3>
                    <span class="badge" style="background:rgba(255,255,255,0.1); font-size:0.7rem;">${v.type.toUpperCase()}</span>
                </div>
                <div style="display:flex; gap:8px;">
                    <button class="btn btn-secondary btn-sm" onclick="playVoicePreview('${v.name}', '${v.type}', '${v.value.replace(/'/g, "\\'")}')" aria-label="Play voice preview" title="Play Preview"><i class="fas fa-play"></i></button>
                    <button class="btn btn-secondary btn-sm" onclick="deleteVoice('${v.id}')" style="color:var(--danger)" aria-label="Delete voice" title="Delete Voice"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `;
        grid.appendChild(div);
    });
}

async function playVoicePreview(role, type, value) {
    const blob = await getVoicePreview({ role, type, value });
    if (blob) {
        const player = document.getElementById('preview-player');
        player.src = URL.createObjectURL(blob);
        player.play();
    }
}

function deleteVoice(id) {
    if (confirm("Delete voice?")) { SpeakerStore.deleteVoice(id); renderVoiceLibrary(); renderSpeechVoiceList(); }
}

// --- Project Studio ---
function toggleCanvasView(view) {
    document.getElementById('canvas-draft-view').style.display = view === 'draft' ? 'flex' : 'none';
    document.getElementById('canvas-production-view').style.display = view === 'production' ? 'flex' : 'none';
    if (view === 'production') renderBlocks();
}

function renderBlocks() {
    const container = document.getElementById('blocks-container');
    if (!container) return;
    container.innerHTML = '';
    CanvasManager.blocks.forEach(block => {
        const div = document.createElement('div');
        div.className = 'story-block';
        div.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="display:flex; align-items:center; gap:12px;">
                    ${renderAvatar(block.role)}
                    <span class="label" style="color:var(--accent); margin:0;">${block.role}</span>
                </div>
                <div style="display:flex; gap:8px; align-items:center;">
                    <select class="btn btn-secondary btn-sm" style="font-size:0.7rem;" onchange="updateBlockProperty('${block.id}', 'language', this.value)">
                        <option value="auto" ${block.language === 'auto' ? 'selected' : ''}>Auto</option>
                        <option value="en" ${block.language === 'en' ? 'selected' : ''}>EN</option>
                        <option value="zh" ${block.language === 'zh' ? 'selected' : ''}>ZH</option>
                        <option value="ja" ${block.language === 'ja' ? 'selected' : ''}>JA</option>
                        <option value="es" ${block.language === 'es' ? 'selected' : ''}>ES</option>
                    </select>
                    <div style="display:flex; align-items:center; gap:4px; font-size:0.7rem; color:var(--text-secondary);">
                        Gap: <input type="number" step="0.1" value="${block.pause_after}" style="width:40px; background:none; border:1px solid var(--border); color:inherit; border-radius:4px; padding:2px;" onchange="updateBlockProperty('${block.id}', 'pause_after', this.value)">s
                    </div>
                    <button class="btn btn-secondary btn-sm" onclick="generateBlock('${block.id}')">${block.status === 'ready' ? 'Regen' : 'Synth'}</button>
                    <button class="btn btn-secondary btn-sm" onclick="deleteBlock('${block.id}')" aria-label="Delete block" title="Delete Block"><i class="fas fa-times"></i></button>
                </div>
            </div>
            <p style="margin: 12px 0; color:var(--text-primary); font-size:0.95rem;">${block.text}</p>
            ${block.status === 'generating' ? `<div class="progress-container"><div class="progress-bar" style="width: ${block.progress}%"></div></div>` : ''}
            ${block.audioUrl ? `<button class="btn btn-primary btn-sm" onclick="playBlock('${block.id}')"><i class="fas fa-play"></i> Play</button>` : ''}
        `;
        container.appendChild(div);
    });
}

function updateBlockProperty(id, prop, val) {
    const block = CanvasManager.blocks.find(b => b.id === id);
    if (block) {
        block[prop] = prop === 'pause_after' ? parseFloat(val) : val;
        CanvasManager.save();
    }
}

async function promoteToProduction() {
    const script = parseScript(document.getElementById('script-editor').value);
    if (script.length === 0) return alert("Write script first (e.g., [Alice]: Hello)");
    CanvasManager.clear();
    script.forEach(line => CanvasManager.addBlock(line.role, line.text));
    CanvasManager.save();
    renderBlocks();
    toggleCanvasView('production');
}

async function generateBlock(id) {
    const block = CanvasManager.blocks.find(b => b.id === id);
    if (!block) return;
    block.status = 'generating'; block.progress = 0; renderBlocks();
    const profiles = getAllProfiles();
    try {
        const res = await fetch('/api/generate/segment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profiles,
                script: [{
                    role: block.role,
                    text: block.text,
                    language: block.language,
                    pause_after: block.pause_after
                }]
            })
        });
        const { task_id } = await res.json();
        const blob = await TaskPoller.poll(task_id, (task) => { block.progress = task.progress; renderBlocks(); });
        block.audioUrl = URL.createObjectURL(blob);
        block.status = 'ready'; renderBlocks();
    } catch (e) { block.status = 'error'; alert(e.message); renderBlocks(); }
}

function playBlock(id) {
    const block = CanvasManager.blocks.find(b => b.id === id);
    if (block && block.audioUrl) {
        const player = document.getElementById('main-audio-player');
        player.src = block.audioUrl;
        player.play();
    }
}

function deleteBlock(id) { CanvasManager.deleteBlock(id); renderBlocks(); }

async function generatePodcast(btn) {
    if (btn) {
        btn.disabled = true;
        btn.setAttribute('aria-busy', 'true');
        btn.dataset.originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Producing...';
    }
    const inProd = document.getElementById('canvas-production-view').style.display === 'flex';
    const script = inProd ? CanvasManager.blocks.map(b => ({
        role: b.role,
        text: b.text,
        language: b.language,
        pause_after: b.pause_after
    })) : parseScript(document.getElementById('script-editor').value);

    if (script.length === 0) return alert("Empty script.");
    const profiles = getAllProfiles();
    const bgm_mood = document.getElementById('bgm-select').value;
    const statusText = document.getElementById('status-text');
    statusText.innerText = "Producing Final Mix...";

    try {
        const res = await fetch('/api/generate/podcast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profiles, script, bgm_mood })
        });
        const { task_id } = await res.json();
        const blob = await TaskPoller.poll(task_id, (task) => { statusText.innerText = `Producing: ${task.progress}%`; });
        const player = document.getElementById('main-audio-player');
        player.src = URL.createObjectURL(blob);
        player.play();
        statusText.innerText = "Final Mix Ready!";
    } catch (e) { alert(e.message); statusText.innerText = "Failed"; }
    finally {
        if (btn) {
            btn.disabled = false;
            btn.removeAttribute('aria-busy');
            btn.innerHTML = btn.dataset.originalHtml;
        }
    }
}

async function batchSynthesize() {
    const blocks = CanvasManager.blocks.filter(b => b.status !== 'ready');
    for (const b of blocks) await generateBlock(b.id);
}

// --- Dubbing & S2S ---
async function startDubbing(btn) {
    if (btn) {
        btn.disabled = true;
        btn.setAttribute('aria-busy', 'true');
        btn.dataset.originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Dubbing...';
    }
    const fileInput = document.getElementById('dub-file');
    const langSelect = document.getElementById('dub-lang');
    const statusText = document.getElementById('status-text');

    const file = fileInput.files[0];
    if (!file) return alert("Please upload a file first.");

    statusText.innerText = "Initiating Dubbing...";

    try {
        const formData = new FormData();
        formData.append('file', file);
        const uploadRes = await fetch('/api/voice/upload', { method: 'POST', body: formData });
        const uploadData = await uploadRes.json();
        const path = uploadData.filename;
        
        const res = await fetch('/api/generate/dub', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source_audio: path, target_lang: langSelect.value })
        });
        
        const { task_id } = await res.json();
        const blob = await TaskPoller.poll(task_id, (task) => {
            statusText.innerText = `Dubbing: ${task.progress}%`;
        });

        const player = document.getElementById('main-audio-player');
        player.src = URL.createObjectURL(blob);
        player.play();
        statusText.innerText = "Dubbing Complete!";
    } catch (e) {
        alert(e.message);
        statusText.innerText = "Dubbing failed";
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.removeAttribute('aria-busy');
            btn.innerHTML = btn.dataset.originalHtml;
        }
    }
}

async function startVoiceChanger(btn) {
    if (!state.s2s.lastUploadedPath) return alert("Record or upload source audio first.");
    if (btn) {
        btn.disabled = true;
        btn.setAttribute('aria-busy', 'true');
        btn.dataset.originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Converting...';
    }
    const targetVoice = JSON.parse(document.getElementById('s2s-target-voice').value);
    const preserveProsody = document.getElementById('s2s-preserve').checked;
    const statusText = document.getElementById('status-text');

    statusText.innerText = "Converting Voice...";
    try {
        const res = await fetch('/api/generate/s2s', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source_audio: state.s2s.lastUploadedPath,
                target_voice: targetVoice,
                preserve_prosody: preserveProsody
            })
        });
        const { task_id } = await res.json();
        const blob = await TaskPoller.poll(task_id, (task) => {
            statusText.innerText = `Converting: ${task.progress}%`;
        });
        const player = document.getElementById('main-audio-player');
        player.src = URL.createObjectURL(blob);
        player.play();
        statusText.innerText = "Conversion Complete!";
    } catch (e) { alert(e.message); statusText.innerText = "Failed"; }
    finally {
        if (btn) {
            btn.disabled = false;
            btn.removeAttribute('aria-busy');
            btn.innerHTML = btn.dataset.originalHtml;
        }
    }
}

    const s2sRecordBtn = document.getElementById('s2s-record-btn');
    if (s2sRecordBtn) s2sRecordBtn.onclick = () => {
        if (state.s2s.isRecording) stopRecording(state.s2s, 's2s-record-btn', '<i class="fas fa-circle"></i> Record Audio');
        else startRecording(state.s2s, 's2s-record-btn', async (blobs) => {
            const formData = new FormData(); formData.append('file', blobs[0]);
            const res = await fetch('/api/voice/upload', { method: 'POST', body: formData });
            const data = await res.json();
            state.s2s.lastUploadedPath = data.filename;
            alert("Recording uploaded.");
        });
    };
}

// Recording utilities (kept here or moved to utils.js)
async function startRecording(targetState, btnId, onComplete) {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        targetState.mediaRecorder = new MediaRecorder(stream);
        targetState.audioChunks = [];
        targetState.mediaRecorder.ondataavailable = (e) => targetState.audioChunks.push(e.data);
        targetState.mediaRecorder.onstop = async () => {
            const blob = new Blob(targetState.audioChunks, { type: 'audio/wav' });
            if (onComplete) onComplete([blob]);
        };
        targetState.mediaRecorder.start();
        targetState.isRecording = true;
        document.getElementById(btnId).innerHTML = '<i class="fas fa-stop"></i> Stop';
        document.getElementById(btnId).classList.add('btn-danger');
    } catch (e) { alert("Mic access denied"); }
}

function stopRecording(targetState, btnId, originalHtml) {
    if (targetState.mediaRecorder) targetState.mediaRecorder.stop();
    targetState.isRecording = false;
    document.getElementById(btnId).innerHTML = originalHtml;
    document.getElementById(btnId).classList.remove('btn-danger');
}

// --- Globals for HTML handlers ---
Object.assign(window, {
    switchView,
    generateSpeech,
    testVoiceDesign,
    playDesignPreview,
    saveDesignedVoice,
    handleCloneUpload,
    testVoiceClone,
    playClonePreview,
    saveClonedVoice,
    testVoiceMix,
    playMixPreview,
    saveMixedVoice,
    uploadVoiceImage, TimelineManager,
    deleteVoice,
    startDubbing,
    startVoiceChanger,
    fetchProjects,
    saveProject,
    loadProject,
    promoteToProduction,
    toggleCanvasView,
    generateBlock,
    playBlock,
    deleteBlock,
    generatePodcast,
    batchSynthesize,
    generateVideo,
    updateBlockProperty,
    renderSystemView,
    downloadModel,
    renderVoiceLibrary,
    renderSpeechVoiceList
});
