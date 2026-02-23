// --- Qwen-TTS Studio Frontend ---

const state = {
    currentView: 'home',
    voicelab: {
        lastDesignedPath: null,
        lastClonedPath: null,
        lastMixedPath: null,
        isRecording: false,
        mediaRecorder: null,
        audioChunks: []
    },
    s2s: {
        lastUploadedPath: null,
        isRecording: false,
        mediaRecorder: null,
        audioChunks: []
    }
};

function renderAvatar(name, imageUrl) {
    if (imageUrl) {
        return `<img src="${imageUrl}" class="avatar" style="object-fit: cover;">`;
    }
    const initials = (name || "??").substring(0, 2).toUpperCase();
    return `<div class="avatar">${initials}</div>`;
}

function switchView(view) {
    state.currentView = view;
    document.querySelectorAll('.view-container').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(v => v.classList.remove('active'));

    const viewEl = document.getElementById(`${view}-view`);
    if (viewEl) viewEl.classList.add('active');

    const navBtn = document.querySelector(`button[onclick="switchView('${view}')"]`);
    if (navBtn) navBtn.classList.add('active');

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
    if (view === 'projects') {
        fetchProjects();
    }
}

// --- Voice Studio ---

async function generateSpeech() {
    const text = document.getElementById('speech-text').value;
    const voiceVal = document.getElementById('speech-voice').value;
    if (!voiceVal) return alert('Select a voice first');

    const voice = JSON.parse(voiceVal);
    const lang = document.getElementById('speech-lang').value;
    const statusText = document.getElementById('status-text');

    if (!text) return alert('Enter text');
    statusText.innerText = 'Generating...';

    try {
        const res = await fetch('/api/generate/segment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profiles: [{ role: 'user', ...voice }],
                script: [{ role: 'user', text, language: lang }]
            })
        });
        const { task_id } = await res.json();
        const blob = await TaskPoller.poll(task_id, (task) => {
            statusText.innerText = 'Generating: ' + task.progress + '%';
        });
        const player = document.getElementById('main-audio-player');
        player.src = URL.createObjectURL(blob);
        player.play();
        statusText.innerText = 'Ready';
    } catch (e) {
        alert(e.message);
        statusText.innerText = 'Failed';
    }
}

function renderSpeechVoiceList() {
    const selects = ['mix-voice-a', 'mix-voice-b', 'speech-voice', 's2s-target-voice'];
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
    el.innerHTML = '';
    getAllProfiles().forEach(p => {
        const opt = document.createElement('option');
        opt.value = JSON.stringify(p);
        opt.innerText = p.role;
        el.appendChild(opt);
    });
}

// --- Voice Lab ---

async function testVoiceDesign(btn) {
    const prompt = document.getElementById('design-prompt').value;
    const gender = document.getElementById('design-gender').value;
    const age = document.getElementById('design-age').value;
    const statusText = document.getElementById('status-text');

    if (!prompt) return alert("Describe the voice");
    const instruct = `${prompt}. Gender: ${gender}, Age: ${age}`;

    if (btn) btn.disabled = true;
    statusText.innerText = "Designing voice...";

    try {
        const res = await fetch('/api/generate/segment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profiles: [{ role: 'preview', type: 'design', value: instruct }],
                script: [{ role: 'preview', text: "This is a preview of my designed voice." }]
            })
        });
        const { task_id } = await res.json();
        const blob = await TaskPoller.poll(task_id);

        window.designPreviewUrl = URL.createObjectURL(blob);
        state.voicelab.lastDesignedPath = instruct;
        document.getElementById('design-preview-container').style.display = 'block';
        statusText.innerText = "Ready";
    } catch (e) { alert(e.message); }
    finally { if (btn) btn.disabled = false; }
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
    const formData = new FormData();
    for (let f of files) formData.append('file', f);

    try {
        const res = await fetch('/api/voice/upload', { method: 'POST', body: formData });
        const data = await res.json();
        state.voicelab.lastClonedPath = data.filename;
        alert("Audio uploaded successfully.");
    } catch (e) { alert("Upload failed"); }
}

async function testVoiceClone(btn) {
    if (!state.voicelab.lastClonedPath) return alert("Upload audio first");
    const statusText = document.getElementById('status-text');
    if (btn) btn.disabled = true;
    statusText.innerText = "Cloning voice...";

    try {
        const res = await fetch('/api/generate/segment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profiles: [{ role: 'preview', type: 'clone', value: state.voicelab.lastClonedPath }],
                script: [{ role: 'preview', text: "This is a preview of my cloned voice." }]
            })
        });
        const { task_id } = await res.json();
        const blob = await TaskPoller.poll(task_id);
        window.clonePreviewUrl = URL.createObjectURL(blob);
        document.getElementById('clone-preview-container').style.display = 'block';
        statusText.innerText = "Ready";
    } catch (e) { alert(e.message); }
    finally { if (btn) btn.disabled = false; }
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
    const vA = JSON.parse(document.getElementById('mix-voice-a').value);
    const vB = JSON.parse(document.getElementById('mix-voice-b').value);
    const wA = document.getElementById('mix-weight-a').value / 100;
    const wB = document.getElementById('mix-weight-b').value / 100;

    const mixConfig = [
        { profile: vA, weight: wA },
        { profile: vB, weight: wB }
    ];

    const statusText = document.getElementById('status-text');
    if (btn) btn.disabled = true;
    statusText.innerText = "Mixing voices...";

    try {
        const res = await fetch('/api/generate/segment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profiles: [{ role: 'preview', type: 'mix', value: JSON.stringify(mixConfig) }],
                script: [{ role: 'preview', text: "This is a preview of my mixed voice." }]
            })
        });
        const { task_id } = await res.json();
        const blob = await TaskPoller.poll(task_id);
        window.mixPreviewUrl = URL.createObjectURL(blob);
        state.voicelab.lastMixedPath = JSON.stringify(mixConfig);
        document.getElementById('mix-preview-container').style.display = 'block';
        statusText.innerText = "Ready";
    } catch (e) { alert(e.message); }
    finally { if (btn) btn.disabled = false; }
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
    const grid = document.getElementById("voice-library-grid");
    if (!grid) return;
    grid.innerHTML = "";

    const voices = SpeakerStore.getVoices();
    voices.forEach(v => {
        const div = document.createElement("div");
        div.className = "card";
        div.style.padding = "20px";
        div.style.display = "flex";
        div.style.flexDirection = "column";
        div.style.gap = "16px";

        const escapedValue = (v.value || "").replace(/'/g, "\\'");

        div.innerHTML = `
            <div style="display:flex; align-items:center; gap:16px;">
                ${renderAvatar(v.name, v.image_url)}
                <div style="flex:1">
                    <h3 style="margin:0; font-size:1rem; font-weight:600;">${v.name}</h3>
                    <span class="badge">${v.type.toUpperCase()}</span>
                </div>
            </div>
            <div style="display:flex; gap:8px; border-top:1px solid var(--border); padding-top:12px;">
                <button class="btn btn-secondary btn-sm" style="flex:1" onclick="playVoicePreview('${v.name}', '${v.type}', '${escapedValue}')" title="Play Preview"><i class="fas fa-play"></i> Preview</button>
                <button class="btn btn-secondary btn-sm" onclick="document.getElementById('img-upload-${v.id}').click()" title="Change Image"><i class="fas fa-image"></i></button>
                <input type="file" id="img-upload-${v.id}" style="display:none" accept="image/*" onchange="uploadVoiceImage('${v.id}', this.files[0])">
                <button class="btn btn-secondary btn-sm" onclick="deleteVoice('${v.id}')" style="color:var(--danger)" title="Delete Voice"><i class="fas fa-trash"></i></button>
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
        div.style.background = 'white';
        div.style.boxShadow = 'var(--shadow-sm)';

        div.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <div style="display:flex; align-items:center; gap:12px;">
                    ${renderAvatar(block.role)}
                    <span style="font-weight:600; font-size:0.9rem;">${block.role}</span>
                </div>
                <div style="display:flex; gap:12px; align-items:center;">
                    <select class="btn btn-secondary btn-sm" style="font-size:0.75rem; background:var(--bg-sidebar); border:none;" onchange="updateBlockProperty('${block.id}', 'language', this.value)">
                        <option value="auto" ${block.language === 'auto' ? 'selected' : ''}>Auto Detect</option>
                        <option value="en" ${block.language === 'en' ? 'selected' : ''}>English</option>
                        <option value="zh" ${block.language === 'zh' ? 'selected' : ''}>Chinese</option>
                        <option value="ja" ${block.language === 'ja' ? 'selected' : ''}>Japanese</option>
                        <option value="es" ${block.language === 'es' ? 'selected' : ''}>Spanish</option>
                    </select>
                    <div style="font-size:0.75rem; color:var(--text-secondary); display:flex; align-items:center; gap:6px;">
                        Pause: <input type="number" step="0.1" value="${block.pause_after}" style="width:50px; background:var(--bg-sidebar); border:none; border-radius:6px; padding:4px 8px; font-size:0.75rem;" onchange="updateBlockProperty('${block.id}', 'pause_after', this.value)">s
                    </div>
                    <button class="btn btn-secondary btn-sm" onclick="deleteBlock('${block.id}')" title="Remove"><i class="fas fa-times"></i></button>
                </div>
            </div>
            <p style="margin: 0 0 16px; color:var(--text-primary); line-height:1.6; font-size:1rem;">${block.text}</p>
            <div style="display:flex; align-items:center; gap:12px;">
                <button class="btn ${block.status === 'ready' ? 'btn-secondary' : 'btn-primary'} btn-sm" onclick="generateBlock('${block.id}')">
                    <i class="fas ${block.status === 'ready' ? 'fa-redo' : 'fa-magic'}"></i> ${block.status === 'ready' ? 'Regenerate' : 'Synthesize'}
                </button>
                ${block.audioUrl ? `<button class="btn btn-secondary btn-sm" onclick="playBlock('${block.id}')"><i class="fas fa-play"></i> Play Audio</button>` : ''}
                ${block.status === 'generating' ? `<div class="progress-container" style="flex:1; margin:0;"><div class="progress-bar" style="width: ${block.progress}%"></div></div>` : ''}
            </div>
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
                profiles: profiles,
                script: [{ role: block.role, text: block.text, language: block.language }]
            })
        });
        const { task_id } = await res.json();
        const blob = await TaskPoller.poll(task_id, (task) => {
            block.progress = task.progress;
            renderBlocks();
        });
        block.audioUrl = URL.createObjectURL(blob);
        block.status = 'ready';
        renderBlocks();
    } catch (e) { block.status = 'error'; renderBlocks(); alert(e.message); }
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
    const script = CanvasManager.blocks.map(b => ({ role: b.role, text: b.text, language: b.language, pause_after: b.pause_after }));
    if (script.length === 0) return alert("Empty script.");
    const profiles = getAllProfiles();
    const bgm = document.getElementById('bgm-select').value;
    const statusText = document.getElementById('status-text');

    if (btn) btn.disabled = true;
    statusText.innerText = "Producing podcast...";

    try {
        const res = await fetch('/api/generate/podcast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profiles, script, bgm_mood: bgm })
        });
        const { task_id } = await res.json();
        const blob = await TaskPoller.poll(task_id, (task) => { statusText.innerText = `Producing: ${task.progress}%`; });
        const player = document.getElementById('main-audio-player');
        player.src = URL.createObjectURL(blob);
        player.play();
        statusText.innerText = 'Ready';
    } catch (e) { alert(e.message); statusText.innerText = "Failed"; }
    finally { if (btn) btn.disabled = false; }
}

async function batchSynthesize() {
    for (let block of CanvasManager.blocks) {
        if (block.status !== 'ready') await generateBlock(block.id);
    }
}

// --- Dubbing & S2S ---

async function startDubbing() {
    const fileInput = document.getElementById('dub-file');
    const langSelect = document.getElementById('dub-lang');
    const statusText = document.getElementById('status-text');
    const file = fileInput.files[0];
    if (!file) return alert("Please upload a file first.");

    statusText.innerText = "Uploading audio...";
    const formData = new FormData(); formData.append('file', file);
    try {
        const uploadRes = await fetch('/api/voice/upload', { method: 'POST', body: formData });
        const { filename: path } = await uploadRes.json();
        
        statusText.innerText = "Dubbing in progress...";
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
    } catch (e) { alert(e.message); statusText.innerText = "Dubbing failed"; }
}

async function startVoiceChanger() {
    if (!state.s2s.lastUploadedPath) return alert("Record or upload source audio first.");
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
    const data = {
        name,
        blocks: CanvasManager.blocks.map(b => ({ id: b.id, role: b.role, text: b.text, status: b.status, language: b.language, pause_after: b.pause_after })),
        script_draft: document.getElementById('script-editor').value,
        voices: SpeakerStore.getVoices()
    };
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

// --- Video ---

async function uploadVoiceImage(voiceId, file) {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
        const res = await fetch("/api/voice/image/upload", { method: "POST", body: formData });
        const data = await res.json();
        SpeakerStore.updateVoice(voiceId, { image_url: data.url });
        renderVoiceLibrary();
        alert("Image uploaded!");
    } catch (e) { alert("Upload failed: " + e.message); }
}

async function generateVideo(btn) {
    const projectName = document.getElementById("project-select").value;
    if (!projectName) return alert("Please save/select a project first.");

    const aspectRatio = document.getElementById("video-aspect").value;
    const includeSubtitles = document.getElementById("video-subtitles").checked;
    const font_size = parseInt(document.getElementById("video-font-size").value) || 40;
    const font_type = document.getElementById("video-font-type").value || "DejaVuSans-Bold.ttf";
    const statusText = document.getElementById("status-text");

    if (btn) btn.disabled = true;
    statusText.innerText = "Generating Video (this takes time)...";
    try {
        await saveProject();

        const res = await fetch("/api/generate/video", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                project_name: projectName,
                aspect_ratio: aspectRatio,
                include_subtitles: includeSubtitles,
                font_size: font_size,
                font_type: font_type
            })
        });
        const { task_id } = await res.json();
        const blob = await TaskPoller.poll(task_id, (task) => {
            statusText.innerText = `Video: ${task.progress}% - ${task.message}`;
        });

        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${projectName}_video.mp4`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        statusText.innerText = "Video Generation Complete! Download started.";
    } catch (e) { alert(e.message); statusText.innerText = "Video failed"; }
    finally { if (btn) btn.disabled = false; }
}

// --- Utilities ---

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

function setupEventListeners() {
    const cloneRecordBtn = document.getElementById('clone-record-btn');
    if (cloneRecordBtn) cloneRecordBtn.onclick = () => {
        if (state.voicelab.isRecording) stopRecording(state.voicelab, 'clone-record-btn', '<i class="fas fa-circle"></i> Record');
        else startRecording(state.voicelab, 'clone-record-btn', (blobs) => handleCloneUpload(blobs));
    };

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

// --- System ---

async function renderSystemView() {
    const invList = document.getElementById('model-inventory-list');
    const stats = document.getElementById('system-stats');
    if (!invList || !stats) return;

    try {
        const res = await fetch('/api/models/inventory');
        const data = await res.json();
        invList.innerHTML = '';
        data.models.forEach(m => {
            const div = document.createElement('div');
            div.style.padding = '12px';
            div.style.background = 'var(--bg-sidebar)';
            div.style.border = '1px solid var(--border)';
            div.style.borderRadius = '10px';
            div.style.display = 'flex';
            div.style.justifyContent = 'space-between';
            div.style.alignItems = 'center';

            div.innerHTML = `
                <div>
                    <div style="font-weight:600; font-size:0.9rem;">${m.key}</div>
                    <div style="font-size:0.75rem; color:var(--text-secondary);">${m.repo_id}</div>
                </div>
                <div>
                    ${m.status === 'downloaded'
                        ? '<span class="badge" style="background:var(--success); color:white;">Ready</span>'
                        : `<button class="btn btn-primary btn-sm" onclick="downloadModel('${m.repo_id}')"><i class="fas fa-download"></i> Download</button>`}
                </div>
            `;
            invList.appendChild(div);
        });
    } catch (e) { invList.innerText = "Failed to load inventory"; }

    try {
        const res = await fetch('/api/health');
        const data = await res.json();
        stats.innerHTML = `
            <div style="margin-bottom:8px;"><strong>Status:</strong> ${data.status}</div>
            <div style="margin-bottom:8px;"><strong>Device:</strong> ${data.device.type} (CUDA: ${data.device.cuda_available})</div>
            <div style="margin-bottom:8px;"><strong>CPU:</strong> ${data.performance.cpu_percent}%</div>
            <div style="margin-bottom:8px;"><strong>Memory:</strong> ${data.performance.memory_percent}%</div>
        `;
    } catch (e) { stats.innerText = "Failed to load stats"; }
}

async function downloadModel(repoId) {
    const statusText = document.getElementById('status-text');
    statusText.innerText = `Starting download for ${repoId}...`;
    try {
        const res = await fetch('/api/models/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ repo_id: repoId })
        });
        const { task_id } = await res.json();
        await TaskPoller.poll(task_id, (task) => {
            statusText.innerText = `Downloading ${repoId}: ${task.progress}%`;
        });
        statusText.innerText = "Download complete!";
        renderSystemView();
    } catch (e) {
        alert("Download failed: " + e.message);
        statusText.innerText = "Download failed";
    }
}

window.onload = () => {
    switchView('home');
    setupEventListeners();
    setInterval(() => {
        const dot = document.getElementById('heartbeat');
        if (dot) { dot.style.opacity = '1'; setTimeout(() => dot.style.opacity = '0.3', 200); }
    }, 2000);
};

Object.assign(window, {
    batchSynthesize,
    deleteBlock,
    deleteVoice,
    downloadModel,
    generateBlock,
    generatePodcast,
    generateSpeech,
    generateVideo,
    handleCloneUpload,
    loadProject,
    playBlock,
    playClonePreview,
    playDesignPreview,
    playMixPreview,
    playVoicePreview,
    promoteToProduction,
    renderSpeechVoiceList,
    renderVoiceLibrary,
    saveClonedVoice,
    saveDesignedVoice,
    saveMixedVoice,
    saveProject,
    startDubbing,
    startVoiceChanger,
    switchView,
    testVoiceClone,
    testVoiceDesign,
    testVoiceMix,
    toggleCanvasView,
    updateBlockProperty,
    uploadVoiceImage
});
