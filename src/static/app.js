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

function escapeHTML(str) {
    const p = document.createElement('p');
    p.textContent = str;
    return p.innerHTML;
}

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
        const heading = targetView.querySelector('h1');
        if (heading) heading.focus();
    }

    const navBtn = document.querySelector(`button[onclick*="${view}"]`);
    if (navBtn) {
        navBtn.classList.add('active');
        navBtn.setAttribute('aria-pressed', 'true');
    }

    if (view === 'assets') {
        loadAssets();
        setupDragAndDrop();
    }
    if (view === 'system') {
        refreshTasks();
    }
}

async function startDubbing() {
    const fileInput = document.getElementById('dub-file');
    const langSelect = document.getElementById('dub-lang');
    const statusText = document.getElementById('status-text') || document.getElementById('status-badge');

    const file = fileInput.files[0];
    if (!file) return alert("Please upload a file first.");

    if (statusText) statusText.innerText = "Initiating Dubbing...";

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
        const data = await res.json();
        pollTask(data.task_id);
    } catch (err) {
        if (statusText) statusText.innerText = "Dubbing Error";
        console.error(err);
    }
}

function pollTask(taskId) {
    const statusText = document.getElementById('status-text') || document.getElementById('status-badge');

    const interval = setInterval(async () => {
        try {
            const res = await fetch(`/api/tasks/${taskId}`);
            const data = await res.json();

            if (data.status === 'completed') {
                clearInterval(interval);
                if (statusText) statusText.innerText = "Task Ready";
                const audioRes = await fetch(`/api/tasks/${taskId}/result`);
                const blob = await audioRes.blob();
                const url = URL.createObjectURL(blob);
                const player = document.getElementById('main-audio-player');
                if (player) {
                    player.src = url;
                    player.play();
                }
                alert("Generation Complete!");
            } else if (data.status === 'failed') {
                clearInterval(interval);
                if (statusText) statusText.innerText = "Task Failed";
                alert(`Error: ${data.error}`);
            } else {
                if (statusText) statusText.innerText = `Processing: ${data.progress}% - ${data.message}`;
            }
        } catch (err) {
            console.error("Polling error", err);
        }
    }, 2000);
}

// --- Shared Assets ---

async function loadAssets() {
    const grid = document.getElementById('asset-library-grid');
    if (!grid) return;
    grid.innerHTML = '<div class="empty-state empty-state-grid"><h3><i class="fas fa-spinner fa-spin"></i> Loading assets...</h3></div>';

    try {
        const resp = await fetch('/api/assets/');
        const assets = await resp.json();

        if (assets.length === 0) {
            grid.innerHTML = `
                <div class="empty-state empty-state-grid">
                    <i class="fas fa-cloud-upload-alt"></i>
                    <h3>No assets found</h3>
                    <p>Drag and drop files here or use the upload button above.</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = assets.map(asset => {
            const isAudio = asset.name.endsWith('.mp3') || asset.name.endsWith('.wav');
            const icon = isAudio ? 'fa-file-audio' : 'fa-file';
            return `
                <div class="card asset-card" style="display:flex; align-items:center; gap:16px;">
                    <div class="asset-icon"><i class="fas ${icon}"></i></div>
                    <div style="flex:1;">
                        <strong style="display:block; font-size:0.95rem;">${asset.name}</strong>
                        <span style="font-size:0.8rem; color:var(--text-secondary);">${(asset.size / 1024 / 1024).toFixed(2)} MB</span>
                    </div>
                    <div style="display:flex; gap:8px;">
                        ${isAudio ? `<button class="btn btn-secondary btn-sm" onclick="playAsset('${asset.name}')" title="Play" aria-label="Play ${asset.name}"><i class="fas fa-play" aria-hidden="true"></i></button>` : ''}
                        <button class="btn btn-danger btn-sm" onclick="deleteAsset('${asset.name}')" title="Delete" aria-label="Delete ${asset.name}"><i class="fas fa-trash" aria-hidden="true"></i></button>
                    </div>
                </div>
            `;
        }).join('');

        // Update BGM selectors
        const bgmSelect = document.getElementById('bgm-select');
        if (bgmSelect) {
            const currentVal = bgmSelect.value;
            const presets = ['mystery', 'tech', 'joy', 'rain'];
            bgmSelect.innerHTML = '<option value="">None</option>' +
                presets.map(p => `<option value="${p}" ${currentVal === p ? 'selected' : ''}>${p.charAt(0).toUpperCase() + p.slice(1)} (Preset)</option>`).join('') +
                assets.filter(a => a.name.endsWith('.mp3') || a.name.endsWith('.wav')).map(a =>
                    `<option value="${a.name}" ${currentVal === a.name ? 'selected' : ''}>${a.name} (Custom)</option>`
                ).join('');
        }
    } catch (err) {
        console.error("Failed to load assets", err);
        grid.innerHTML = '<div class="empty-state empty-state-grid"><h3>Error loading assets</h3></div>';
    }
}

function setupDragAndDrop() {
    const zone = document.getElementById('assets-view');
    if (!zone) return;

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });

    ['dragleave', 'dragend', 'drop'].forEach(evt => {
        zone.addEventListener(evt, () => zone.classList.remove('drag-over'));
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const input = { files: files };
            uploadAsset(input);
        }
    });
}

async function uploadAsset(input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch('/api/assets/upload', { method: 'POST', body: formData });
        if (resp.ok) loadAssets();
        else alert("Upload failed");
    } catch (err) { console.error("Upload error", err); }
}

async function deleteAsset(name) {
    if (!confirm(`Delete ${name}?`)) return;
    try {
        const resp = await fetch(`/api/assets/${name}`, { method: 'DELETE' });
        if (resp.ok) loadAssets();
    } catch (err) { console.error("Delete error", err); }
}

function playAsset(name) {
    const audio = new Audio(`/api/assets/download/${name}`);
    audio.play();
}

// --- Task Monitor ---

async function refreshTasks() {
    const grids = document.querySelectorAll('.js-task-monitor-list');
    if (grids.length === 0) return;

    try {
        const resp = await fetch('/api/tasks/');
        const tasks = await resp.json();

        const content = tasks.length === 0
            ? '<div class="card" style="border-style:dashed; opacity:0.6; text-align:center;">No active tasks</div>'
            : tasks.sort((a,b) => b.created_at - a.created_at).map(task => `
            <div class="card task-item" style="border-left: 4px solid ${getTaskColor(task.status)};">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
                    <div>
                        <div class="task-item-meta">
                            <strong style="font-size:0.9rem;">${task.type.split('_').join(' ').toUpperCase()}</strong>
                            <span class="task-badge task-badge-${task.status}">${task.status}</span>
                        </div>
                        <div style="font-size:0.75rem; color:var(--text-secondary);">ID: ${task.id.split('-')[0]}... • ${new Date(task.created_at * 1000).toLocaleTimeString()}</div>
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="cancelTask('${task.id}')" ${['completed', 'failed', 'cancelled'].includes(task.status) ? 'disabled' : ''} style="padding: 4px 8px; font-size: 0.7rem;" aria-label="Cancel task">
                        <i class="fas fa-times" aria-hidden="true"></i> Cancel
                    </button>
                </div>

                <div class="progress-bar-container" style="height:6px; margin-bottom:8px;" aria-label="Progress bar">
                    <div class="progress-bar-fill" style="width:${task.progress}%;" aria-valuenow="${task.progress}" aria-valuemin="0" aria-valuemax="100"></div>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size:0.75rem; opacity:0.8; font-style:italic;">${task.message}</div>
                    <div style="font-size:0.75rem; font-weight:700;">${task.progress}%</div>
                </div>
            </div>
        `).join('');

        grids.forEach(grid => { grid.innerHTML = content; });
    } catch (err) { console.error("Failed to load tasks", err); }
}

function getTaskColor(status) {
    switch (status) {
        case 'pending': return 'var(--text-secondary)';
        case 'processing': return 'var(--accent)';
        case 'completed': return 'var(--success)';
        case 'failed': return 'var(--danger)';
        case 'cancelled': return '#f59e0b';
        default: return 'var(--border)';
    }
}

async function cancelTask(id) {
    if (!confirm(`Cancel this task?`)) return;
    try {
        const resp = await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
        if (resp.ok) refreshTasks();
    } catch (err) { console.error("Cancel error", err); }
}

setInterval(() => {
    if (['projects', 'dubbing', 'system'].includes(state.currentView)) refreshTasks();
}, 5000);

// --- Project Studio Features ---

async function exportStudioBundle() {
    const projectSelect = document.getElementById('project-select');
    const projectName = projectSelect.value;
    if (!projectName) return alert("Please select and save a project first.");

    try {
        const resp = await fetch(`/api/projects/${projectName}/export`);
        if (!resp.ok) throw new Error("Export failed");
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${projectName}_bundle.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (err) { alert(`Failed to export bundle: ${err.message}`); }
}

async function generatePodcast() {
    const statusText = document.getElementById('status-badge');
    const bgm_mood = document.getElementById('bgm-select').value;
    const ducking_level = parseFloat(document.getElementById('ducking-range').value) / 100.0;

    const productionView = document.getElementById('canvas-production-view');
    const isProduction = productionView && productionView.style.display === 'flex';

    let script = [];
    if (isProduction) {
        script = CanvasManager.blocks.map(b => ({
            role: b.role,
            text: b.text,
            language: b.language || 'auto',
            pause_after: b.pause_after || 0.5
        }));
    } else {
        script = parseScript(document.getElementById('script-editor').value);
    }

    if (script.length === 0) return alert("Script is empty.");
    const profiles = getAllProfiles();

    try {
        if (statusText) statusText.innerText = "Producing Podcast...";
        const res = await fetch('/api/generate/podcast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profiles, script, bgm_mood, ducking_level })
        });
        if (!res.ok) throw new Error("Podcast request failed");
        const data = await res.json();
        const blob = await TaskPoller.poll(data.task_id, (task) => {
            if (statusText) statusText.innerText = `Producing: ${task.progress}% - ${task.message}`;
        });
        const url = URL.createObjectURL(blob);
        const player = document.getElementById('main-audio-player');
        if (player) { player.src = url; player.play(); }
        if (statusText) statusText.innerText = "Podcast Ready";
    } catch (err) {
        if (statusText) statusText.innerText = "Production Failed";
        alert(`Error: ${err.message}`);
    }
}

// Global exposure
Object.assign(window, {
    switchView,
    startDubbing,
    loadAssets,
    uploadAsset,
    deleteAsset,
    playAsset,
    refreshTasks,
    cancelTask,
    exportStudioBundle,
    generatePodcast,
    setupDragAndDrop
});

async function clearCompletedTasks() {
    try {
        const resp = await fetch('/api/tasks/');
        const tasks = await resp.json();
        const finished = tasks.filter(t => ['completed', 'failed', 'cancelled'].includes(t.status));

        for (const t of finished) {
            // We use the same DELETE endpoint as cancellation,
            // since it's just removing from memory for finished tasks
            await fetch(`/api/tasks/${t.id}`, { method: 'DELETE' });
        }
        refreshTasks();
    } catch (err) { console.error("Clear error", err); }
}

window.clearCompletedTasks = clearCompletedTasks;
