// --- Qwen-TTS Studio Frontend ---

const state = {
    currentView: 'speech',
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

function renderAvatar(name) {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD', '#D4A5A5', '#9B59B6'];
    const color = colors[(name || '').length % colors.length];
    const safeName = escapeHTML(name || '');
    const initial = (name && name.length > 0) ? escapeHTML(name[0].toUpperCase()) : '?';
    return `<div class="avatar" style="background:${color}" title="${safeName}" aria-label="Avatar for ${safeName}">${initial}</div>`;
}

function switchView(view) {
    state.currentView = view;
    document.querySelectorAll('.view-container').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(v => {
        v.classList.remove('active');
        v.setAttribute('aria-pressed', 'false');
    });

    const targetView = document.getElementById(`${view}-view`);
    if (targetView) {
        targetView.classList.add('active');
        // Move focus to the view heading for screen readers
        const heading = targetView.querySelector('h1');
        if (heading) heading.focus();
    }

    const navBtn = document.querySelector(`button[onclick="switchView('${view}')"]`);
    if (navBtn) {
        navBtn.classList.add('active');
        navBtn.setAttribute('aria-pressed', 'true');
    }

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
            <div style="grid-column: 1 / -1; padding: 48px; text-align: center; background: rgba(255,255,255,0.02); border: 2px dashed var(--border); border-radius: 20px;">
                <i class="fas fa-microphone-slash fa-3x" style="color: var(--text-secondary); margin-bottom: 16px; opacity: 0.5;"></i>
                <h3 style="color: var(--text-primary); margin-bottom: 8px;">No custom voices yet</h3>
                <p style="color: var(--text-secondary); font-size: 0.9rem;">Design, clone, or mix voices above to build your library.</p>
            </div>
        `;
        return;
    }

    voices.forEach(v => {
        const div = document.createElement('div');
        div.className = 'card voice-card';
        const escapedName = escapeHTML(v.name);
        div.innerHTML = `
            <div style="display:flex; align-items:center; gap:16px;">
                ${renderAvatar(v.name)}
                <div style="flex:1">
                    <h3 style="margin:0; font-size:1rem;">${escapedName}</h3>
                    <span class="badge" style="background:rgba(255,255,255,0.1); font-size:0.7rem;">${escapeHTML(v.type.toUpperCase())}</span>
                </div>
                <div style="display:flex; gap:8px;">
                    <button class="btn btn-secondary btn-sm js-play" aria-label="Play voice preview" title="Play Preview"><i class="fas fa-play" aria-hidden="true"></i></button>
                    <button class="btn btn-secondary btn-sm js-delete" style="color:var(--danger)" aria-label="Delete voice" title="Delete Voice"><i class="fas fa-trash" aria-hidden="true"></i></button>
                </div>
            </div>
        `;
        div.querySelector('.js-play').onclick = (e) => playVoicePreview(e.currentTarget, v.name, v.type, v.value);
        div.querySelector('.js-delete').onclick = () => deleteVoice(v.id);
        grid.appendChild(div);
    });
}

async function playVoicePreview(btn, role, type, value) {
    if (btn) {
        btn.disabled = true;
        btn.setAttribute('aria-busy', 'true');
        btn.dataset.originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }
    try {
        const blob = await getVoicePreview({ role, type, value });
        if (blob) {
            const player = document.getElementById('preview-player');
            player.src = URL.createObjectURL(blob);
            player.play();
        }
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.removeAttribute('aria-busy');
            btn.innerHTML = btn.dataset.originalHtml;
        }
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

function renderBlockContent(block) {
    const escapedRole = escapeHTML(block.role);
    const escapedText = escapeHTML(block.text);
    return `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div style="display:flex; align-items:center; gap:12px;">
                ${renderAvatar(block.role)}
                <span class="label" style="color:var(--accent); margin:0;">${escapedRole}</span>
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
                <button class="btn btn-secondary btn-sm" onclick="deleteBlock('${block.id}')" aria-label="Delete block" title="Delete Block"><i class="fas fa-times" aria-hidden="true"></i></button>
            </div>
        </div>
        <p style="margin: 12px 0; color:var(--text-primary); font-size:0.95rem;">${escapedText}</p>
        <div class="block-status" id="status-${block.id}">
            ${block.status === 'generating' ? `<div class="progress-container"><div class="progress-bar" style="width: ${block.progress}%"></div></div>` : ''}
            ${block.audioUrl ? `<button class="btn btn-primary btn-sm" onclick="playBlock('${block.id}')"><i class="fas fa-play" aria-hidden="true"></i> Play</button>` : ''}
        </div>
    `;
}

function renderBlocks() {
    const container = document.getElementById('blocks-container');
    if (!container) return;
    container.innerHTML = '';

    if (CanvasManager.blocks.length === 0) {
        container.innerHTML = `
            <div style="padding: 40px; text-align: center; color: var(--text-secondary); background: rgba(0,0,0,0.1); border-radius: 16px; border: 1px dashed var(--border);">
                <i class="fas fa-layer-group fa-2x" style="margin-bottom: 12px; opacity: 0.3;"></i>
                <p>No story blocks yet. Use the Draft tab to write your script, then click "Promote to Blocks".</p>
            </div>
        `;
        return;
    }

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

async function generatePodcast() {
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
}

async function batchSynthesize() {
    const blocks = CanvasManager.blocks.filter(b => b.status !== 'ready');
    for (const b of blocks) await generateBlock(b.id);
}

// --- Dubbing & S2S ---
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
        if (data.voices && data.voices.length > 0) {
            const currentVoices = SpeakerStore.getVoices();
            data.voices.forEach(v => {
                if (!currentVoices.find(cv => cv.id === v.id)) SpeakerStore.saveVoice(v);
            });
            renderVoiceLibrary();
        }
        alert("Loaded!");
    } catch (e) { alert(e.message); }
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
            if (onComplete) onComplete([blob]); // Wrap in list for consistency with handleCloneUpload
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

// --- Setup ---
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

window.onload = async () => {
    await initializePresets();
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
    switchView, playVoicePreview,
    testVoiceDesign, playDesignPreview, saveDesignedVoice,
    handleCloneUpload, testVoiceClone, playClonePreview, saveClonedVoice,
    testVoiceMix, playMixPreview, saveMixedVoice,
    deleteVoice, toggleCanvasView, promoteToProduction, generateBlock,
    playBlock, deleteBlock, generatePodcast, batchSynthesize, saveProject, loadProject,
    startDubbing, startVoiceChanger, updateBlockProperty
});

// --- System Manager ---
async function renderSystemView() {
    const invList = document.getElementById('model-inventory-list');
    const stats = document.getElementById('system-stats');
    if (!invList || !stats) return;

    // Fetch Inventory
    try {
        const res = await fetch('/api/models/inventory');
        const data = await res.json();
        invList.innerHTML = '';
        data.models.forEach(m => {
            const div = document.createElement('div');
            div.style.padding = '12px';
            div.style.background = 'rgba(255,255,255,0.03)';
            div.style.border = '1px solid var(--border)';
            div.style.borderRadius = '10px';
            div.style.display = 'flex';
            div.style.justifyContent = 'space-between';
            div.style.alignItems = 'center';

            const escapedKey = escapeHTML(m.key);
            const escapedRepoId = escapeHTML(m.repo_id);

            div.innerHTML = `
                <div>
                    <div style="font-weight:600; font-size:0.9rem;">${escapedKey}</div>
                    <div style="font-size:0.75rem; color:var(--text-secondary);">${escapedRepoId}</div>
                </div>
                <div class="action-area">
                    ${m.status === 'downloaded'
                        ? '<span class="badge" style="background:var(--success)">Ready</span>'
                        : `<button class="btn btn-primary btn-sm js-download"><i class="fas fa-download"></i> Download</button>`}
                </div>
            `;

            const downloadBtn = div.querySelector('.js-download');
            if (downloadBtn) {
                downloadBtn.onclick = () => downloadModel(m.repo_id);
            }
            invList.appendChild(div);
        });
    } catch (e) { invList.innerText = "Failed to load inventory"; }

    // Fetch Stats
    try {
        const res = await fetch('/api/health');
        const data = await res.json();
        stats.innerHTML = `
            <div style="margin-bottom:8px;"><strong>Status:</strong> ${escapeHTML(data.status)}</div>
            <div style="margin-bottom:8px;"><strong>Device:</strong> ${escapeHTML(data.device.type)} (CUDA: ${escapeHTML(String(data.device.cuda_available))})</div>
            <div style="margin-bottom:8px;"><strong>CPU:</strong> ${escapeHTML(String(data.performance.cpu_percent))}%</div>
            <div style="margin-bottom:8px;"><strong>Memory:</strong> ${escapeHTML(String(data.performance.memory_percent))}%</div>
            <div><strong>Models Dir:</strong> ${escapeHTML(data.models.models_dir_path)}</div>
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

// Update switchView to handle system view
const originalSwitchView = window.switchView;
Object.assign(window, { downloadModel });
