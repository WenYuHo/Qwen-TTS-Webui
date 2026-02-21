/**
 * Qwen Studio - Main Application Logic
 */

// --- State ---
const state = {
    currentView: 'speech',
    speechSubTab: 'tts',
    selectedVoice: null,
    voicelab: {
        designResult: null,
        cloneResult: null,
        lastUploadedPath: null,
        recorder: null,
        audioChunks: [],
        isRecording: false
    },
    s2s: {
        recorder: null,
        audioChunks: [],
        isRecording: false,
        lastUploadedPath: null
    }
};

// --- View Management ---
function switchView(viewId) {
    document.querySelectorAll('.view-container').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    const targetView = document.getElementById(viewId + '-view');
    if (targetView) targetView.classList.add('active');

    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.getAttribute('onclick').includes(viewId)) {
            item.classList.add('active');
        }
    });

    state.currentView = viewId;

    if (viewId === 'voicelab') renderVoiceLibrary();
    if (viewId === 'speech') renderSpeechVoiceList();
}

function switchSpeechSubTab(tab) {
    state.speechSubTab = tab;
    document.getElementById('tts-input').style.display = tab === 'tts' ? 'block' : 'none';
    document.getElementById('s2s-input').style.display = tab === 's2s' ? 'block' : 'none';
}

// --- Recording Utilities ---
async function startRecording(targetState, btnId, callback) {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        targetState.recorder = new MediaRecorder(stream);
        targetState.audioChunks = [];
        targetState.isRecording = true;

        targetState.recorder.ondataavailable = (e) => {
            targetState.audioChunks.push(e.data);
        };

        targetState.recorder.onstop = async () => {
            const blob = new Blob(targetState.audioChunks, { type: 'audio/wav' });
            const file = new File([blob], "recording.wav", { type: 'audio/wav' });
            await callback(file);
            stream.getTracks().forEach(track => track.stop());
        };

        targetState.recorder.start();
        document.getElementById(btnId).innerHTML = '<i class="fas fa-stop"></i> Stop Recording';
        document.getElementById(btnId).classList.replace('btn-danger', 'btn-primary');
    } catch (e) {
        alert("Microphone access denied.");
    }
}

function stopRecording(targetState, btnId, originalHtml) {
    if (targetState.recorder && targetState.isRecording) {
        targetState.recorder.stop();
        targetState.isRecording = false;
        document.getElementById(btnId).innerHTML = originalHtml;
        document.getElementById(btnId).classList.replace('btn-primary', 'btn-danger');
    }
}

// --- Voice List Rendering ---
function renderSpeechVoiceList() {
    const list = document.getElementById('speech-voice-list');
    if (!list) return;
    const voices = getAllProfiles();
    list.innerHTML = '';

    voices.forEach(v => {
        const div = document.createElement('div');
        div.className = 'voice-card' + (state.selectedVoice && state.selectedVoice.role === v.role ? ' selected' : '');
        div.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="flex:1">
                    <strong>${v.role}</strong>
                    <div style="font-size:0.7rem; color:var(--text-secondary);">${v.type.toUpperCase()}</div>
                </div>
                <button class="btn btn-secondary btn-sm" onclick="playVoicePreview('${v.role}', '${v.type}', '${v.value}', event)">
                    <i class="fas fa-play"></i>
                </button>
            </div>
        `;
        div.onclick = () => {
            state.selectedVoice = v;
            renderSpeechVoiceList();
        };
        list.appendChild(div);
    });
}

async function playVoicePreview(role, type, value, event) {
    if (event) event.stopPropagation();
    const player = document.getElementById('preview-player');
    const blob = await getVoicePreview({ role, type, value });
    if (blob) {
        player.src = URL.createObjectURL(blob);
        player.play();
    }
}

// --- Speech Synthesis ---
async function generateSpeech() {
    if (!state.selectedVoice) return alert("Please select a voice first.");
    const audioPlayer = document.getElementById('main-audio-player');
    const statusText = document.getElementById('status-text');

    if (state.speechSubTab === 'tts') {
        const text = document.getElementById('tts-text').value;
        if (!text) return alert("Please enter some text.");
        statusText.innerText = "Synthesizing...";
        try {
            const profiles = [state.selectedVoice];
            const script = [{ role: state.selectedVoice.role, text: text }];
            const res = await fetch('/api/generate/segment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profiles, script })
            });
            const { task_id } = await res.json();
            const blob = await TaskPoller.poll(task_id, (task) => {
                statusText.innerText = `Synthesizing: ${task.progress}%`;
            });
            audioPlayer.src = URL.createObjectURL(blob);
            audioPlayer.play();
            statusText.innerText = "Speech ready!";
        } catch (e) {
            alert("Error: " + e.message);
            statusText.innerText = "Failed";
        }
    } else {
        if (!state.s2s.lastUploadedPath) return alert("Please upload/record source audio.");
        statusText.innerText = "Transcribing & Synthesizing...";
        try {
            const res = await fetch('/api/generate/s2s', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source_audio: state.s2s.lastUploadedPath, target_voice: state.selectedVoice })
            });
            const { task_id } = await res.json();
            const blob = await TaskPoller.poll(task_id, (task) => {
                statusText.innerText = `Processing: ${task.progress}%`;
            });
            audioPlayer.src = URL.createObjectURL(blob);
            audioPlayer.play();
            statusText.innerText = "S2S Complete!";
        } catch (e) {
            alert(e.message);
            statusText.innerText = "S2S failed";
        }
    }
}

// --- Voice Lab: Design ---
function randomizeDesign() {
    const prompts = [
        "A calm, middle-aged man with a deep and soothing tone",
        "A energetic young woman with a high-pitched, friendly voice",
        "An elderly storyteller with a gravelly, wise-sounding voice",
        "A professional news anchor with a clear, authoritative tone",
        "A soft-spoken person with a gentle, whispering quality"
    ];
    document.getElementById('design-instruct').value = prompts[Math.floor(Math.random() * prompts.length)];
}

async function testVoiceDesign() {
    const instruct = document.getElementById('design-instruct').value;
    const gender = document.getElementById('design-gender').value;
    const age = document.getElementById('design-age').value;
    const accent = document.getElementById('design-accent').value;
    const genderText = gender > 60 ? 'Female' : (gender < 40 ? 'Male' : 'Androgynous');
    const ageText = age < 25 ? 'Young' : (age < 60 ? 'Middle-aged' : 'Elderly');
    const enhancedPrompt = `${instruct}. Voice features: ${genderText}, ${ageText}. Accent intensity: ${accent/100}.`;

    const status = document.getElementById('design-status');
    document.getElementById('design-preview-container').style.display = 'block';
    status.innerText = "Designing...";

    try {
        const profile = { role: 'tester', type: 'design', value: enhancedPrompt };
        const res = await fetch('/api/generate/segment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profiles: [profile], script: [{ role: 'tester', text: "Hello, this is my new custom voice design." }] })
        });
        const { task_id } = await res.json();
        const blob = await TaskPoller.poll(task_id, (task) => {
            status.innerText = `Designing: ${task.progress}%`;
        });
        state.voicelab.designResult = { url: URL.createObjectURL(blob), type: 'design', value: enhancedPrompt };
        status.innerText = "Ready!";
    } catch (e) {
        alert("Error: " + e.message);
        status.innerText = "Failed";
    }
}

function playDesignPreview() {
    if (state.voicelab.designResult) {
        const player = document.getElementById('preview-player');
        player.src = state.voicelab.designResult.url;
        player.play();
    }
}

async function saveDesignedVoice() {
    const result = state.voicelab.designResult;
    if (!result) return;
    const name = prompt("Enter voice name:");
    if (!name) return;
    SpeakerStore.saveVoice({ id: Date.now().toString(), name: name, type: result.type, value: result.value });
    renderVoiceLibrary();
}

// --- Voice Lab: Cloning ---
async function handleCloneUpload(file) {
    if (!file) return;
    document.getElementById('clone-filename').innerText = "Uploading...";
    const formData = new FormData();
    formData.append('file', file);
    try {
        const res = await fetch('/api/voice/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (document.getElementById('clone-mode').value === 'professional' && state.voicelab.lastUploadedPath) {
            state.voicelab.lastUploadedPath += "|" + data.filename;
            document.getElementById('clone-filename').innerText = "✅ Multiple samples";
        } else {
            state.voicelab.lastUploadedPath = data.filename;
            document.getElementById('clone-filename').innerText = "✅ Uploaded: " + file.name;
        }
    } catch (e) { alert(e.message); }
}

async function testVoiceClone() {
    if (!state.voicelab.lastUploadedPath) return alert("Upload/record audio first.");
    const status = document.getElementById('clone-status');
    document.getElementById('clone-preview-container').style.display = 'block';
    status.innerText = "Cloning...";
    try {
        const profile = { role: 'tester', type: 'clone', value: state.voicelab.lastUploadedPath };
        const res = await fetch('/api/generate/segment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profiles: [profile], script: [{ role: 'tester', text: "Testing high-fidelity clone." }] })
        });
        const { task_id } = await res.json();
        const blob = await TaskPoller.poll(task_id, (task) => { status.innerText = `Cloning: ${task.progress}%`; });
        state.voicelab.cloneResult = { url: URL.createObjectURL(blob), type: 'clone', value: state.voicelab.lastUploadedPath };
        status.innerText = "Ready!";
    } catch (e) { alert(e.message); }
}

function playClonePreview() {
    if (state.voicelab.cloneResult) {
        const player = document.getElementById('preview-player');
        player.src = state.voicelab.cloneResult.url;
        player.play();
    }
}

async function saveClonedVoice() {
    const result = state.voicelab.cloneResult;
    if (!result) return;
    const name = prompt("Voice name:");
    if (!name) return;
    SpeakerStore.saveVoice({ id: Date.now().toString(), name, type: 'clone', value: result.value });
    renderVoiceLibrary();
}

// --- Library & Avatar ---
function getAvatarColor(name) {
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
    return '#' + (hash & 0x00FFFFFF).toString(16).toUpperCase().padStart(6, '0');
}

function renderAvatar(name) {
    const color = getAvatarColor(name);
    return `<div class="avatar" style="background:${color}; width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; color:white; font-size:0.8rem; border:2px solid rgba(255,255,255,0.2);">${name.substring(0, 1).toUpperCase()}</div>`;
}

function renderVoiceLibrary() {
    const grid = document.getElementById('voice-library-grid');
    if (!grid) return;
    const voices = SpeakerStore.getVoices();
    grid.innerHTML = voices.length ? '' : '<p style="grid-column: 1/-1; text-align: center; color: var(--text-secondary);">Your library is empty.</p>';
    voices.forEach(v => {
        const div = document.createElement('div');
        div.className = 'card';
        div.style.padding = '16px';
        div.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:12px;">
                    ${renderAvatar(v.name)}
                    <div>
                        <strong>${v.name}</strong>
                        <div style="font-size:0.7rem; color:var(--text-secondary);">${v.type.toUpperCase()}</div>
                    </div>
                </div>
                <div style="display:flex; gap:8px;">
                    <button class="btn btn-secondary btn-sm" onclick="playVoicePreview('${v.name}', '${v.type}', '${v.value}')"><i class="fas fa-play"></i></button>
                    <button class="btn btn-secondary btn-sm" onclick="deleteVoice('${v.id}')" style="color:var(--danger)"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `;
        grid.appendChild(div);
    });
}

function deleteVoice(id) {
    if (confirm("Delete voice?")) { SpeakerStore.deleteVoice(id); renderVoiceLibrary(); renderSpeechVoiceList(); }
}

// --- Project Studio ---
function toggleCanvasView(view) {
    document.getElementById('canvas-draft-view').style.display = view === 'draft' ? 'flex' : 'none';
    document.getElementById('canvas-production-view').style.display = view === 'production' ? 'flex' : 'none';
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
                <div style="display:flex; gap:8px;">
                    <button class="btn btn-secondary btn-sm" onclick="generateBlock('${block.id}')">${block.status === 'ready' ? 'Regen' : 'Synth'}</button>
                    <button class="btn btn-secondary btn-sm" onclick="deleteBlock('${block.id}')"><i class="fas fa-times"></i></button>
                </div>
            </div>
            <p style="margin: 12px 0; color:var(--text-primary);">${block.text}</p>
            ${block.status === 'generating' ? `<div class="progress-container"><div class="progress-bar" style="width: ${block.progress}%"></div></div>` : ''}
            ${block.audioUrl ? `<button class="btn btn-primary btn-sm" onclick="playBlock('${block.id}')"><i class="fas fa-play"></i> Play</button>` : ''}
        `;
        container.appendChild(div);
    });
}

async function promoteToProduction() {
    const script = parseScript(document.getElementById('script-editor').value);
    if (script.length === 0) return alert("Write script first (e.g., Alice: Hello)");
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
            body: JSON.stringify({ profiles, script: [{ role: block.role, text: block.text }] })
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

async function generatePodcast() {
    const inProd = document.getElementById('canvas-production-view').style.display === 'flex';
    const script = inProd ? CanvasManager.blocks.map(b => ({ role: b.role, text: b.text })) : parseScript(document.getElementById('script-editor').value);
    if (script.length === 0) return alert("Empty script.");
    const profiles = getAllProfiles();
    const bgm_mood = document.getElementById('bgm-select').value;
    const statusText = document.getElementById('status-text');
    statusText.innerText = "Producing...";
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
        statusText.innerText = "Ready!";
    } catch (e) { alert(e.message); statusText.innerText = "Failed"; }
}

async function batchSynthesize() {
    const blocks = CanvasManager.blocks.filter(b => b.status !== 'ready');
    for (const b of blocks) await generateBlock(b.id);
}

// --- Dubbing ---
async function startDubbing() {
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
    }
}

// --- Projects ---
async function fetchProjects() {
    const select = document.getElementById('project-select');
    if (!select) return;
    try {
        const res = await fetch('/api/projects');
        const data = await res.json();
        select.innerHTML = '<option value="">(New Project)</option>';
        data.projects.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p; opt.innerText = p; select.appendChild(opt);
        });
    } catch (e) { console.error(e); }
}

async function saveProject() {
    let name = document.getElementById('project-select').value || prompt("Project Name:");
    if (!name) return;
    const data = { name, blocks: CanvasManager.blocks.map(b => ({ id: b.id, role: b.role, text: b.text, status: b.status })), script_draft: document.getElementById('script-editor').value };
    try {
        await fetch(`/api/projects/${name}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        alert("Saved!"); fetchProjects();
    } catch (e) { alert(e.message); }
}

async function loadProject() {
    const name = document.getElementById('project-select').value;
    if (!name) return;
    try {
        const res = await fetch(`/api/projects/${name}`);
        const data = await res.json();
        document.getElementById('script-editor').value = data.script_draft || "";
        CanvasManager.clear();
        (data.blocks || []).forEach(b => { CanvasManager.blocks.push({ ...b, audioUrl: null }); });
        renderBlocks();
        alert("Loaded!");
    } catch (e) { alert(e.message); }
}

// --- Setup ---
function setupEventListeners() {
    const cloneRecordBtn = document.getElementById('clone-record-btn');
    if (cloneRecordBtn) cloneRecordBtn.onclick = () => {
        if (state.voicelab.isRecording) stopRecording(state.voicelab, 'clone-record-btn', '<i class="fas fa-circle"></i> Record');
        else startRecording(state.voicelab, 'clone-record-btn', handleCloneUpload);
    };

    const s2sRecordBtn = document.getElementById('s2s-record-btn');
    if (s2sRecordBtn) s2sRecordBtn.onclick = () => {
        if (state.s2s.isRecording) stopRecording(state.s2s, 's2s-record-btn', '<i class="fas fa-circle"></i> Record Audio');
        else startRecording(state.s2s, 's2s-record-btn', async (file) => {
            const formData = new FormData(); formData.append('file', file);
            const res = await fetch('/api/voice/upload', { method: 'POST', body: formData });
            const data = await res.json();
            state.s2s.lastUploadedPath = data.filename;
            alert("Recording uploaded.");
        });
    };
}

window.onload = () => {
    switchView('speech');
    renderSpeechVoiceList();
    renderVoiceLibrary();
    fetchProjects();
    setupEventListeners();
    setInterval(() => {
        const dot = document.getElementById('heartbeat');
        if (dot) { dot.style.opacity = '1'; setTimeout(() => dot.style.opacity = '0.3', 200); }
    }, 2000);
};

// Globals
Object.assign(window, {
    switchView, switchSpeechSubTab, generateSpeech, playVoicePreview,
    randomizeDesign, testVoiceDesign, playDesignPreview, saveDesignedVoice,
    handleCloneUpload, testVoiceClone, playClonePreview, saveClonedVoice,
    deleteVoice, toggleCanvasView, promoteToProduction, generateBlock,
    playBlock, deleteBlock, generatePodcast, batchSynthesize, saveProject, loadProject,
    startDubbing
});
