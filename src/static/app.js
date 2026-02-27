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

    const navBtn = document.querySelector(`button[onclick="switchView('${view}')"]`);
    if (navBtn) {
        navBtn.classList.add('active');
        navBtn.setAttribute('aria-pressed', 'true');
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

// Global exposure
window.switchView = switchView;
window.startDubbing = startDubbing;
