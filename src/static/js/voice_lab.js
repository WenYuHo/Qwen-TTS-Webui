import { TaskMonitor } from './tasks.js';

export async function generateSpeech() { const type = 'speech';
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
        TaskMonitor.addTask(task_id, type);
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

import { state } from './state.js';
import { TaskPoller } from './api.js';
import { renderVoiceLibrary, renderSpeechVoiceList } from './ui.js';
import { SpeakerStore } from './store.js';

export async function testVoiceDesign(btn) { const type = 'voice_design';
    const prompt = document.getElementById('design-prompt')?.value;
    const gender = document.getElementById('design-gender')?.value;
    const age = document.getElementById('design-age')?.value;
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
        TaskMonitor.addTask(task_id, type);
        const blob = await TaskPoller.poll(task_id);

        window.designPreviewUrl = URL.createObjectURL(blob);
        state.voicelab.lastDesignedPath = instruct;
        const container = document.getElementById('design-preview-container');
        if (container) container.style.display = 'block';
        statusText.innerText = "Ready";
    } catch (e) { alert(e.message); }
    finally { if (btn) btn.disabled = false; }
}

export function playDesignPreview() {
    if (window.designPreviewUrl) {
        const player = document.getElementById('preview-player');
        player.src = window.designPreviewUrl;
        player.play();
    }
}

export function saveDesignedVoice() {
    const name = prompt("Voice Name:");
    if (!name || !state.voicelab.lastDesignedPath) return;
    SpeakerStore.saveVoice({ id: Date.now(), name, type: 'design', value: state.voicelab.lastDesignedPath });
    renderVoiceLibrary();
    renderSpeechVoiceList();
}

export async function handleCloneUpload(files) {
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

export async function testVoiceClone(btn) { const type = 'voice_clone';
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
        TaskMonitor.addTask(task_id, type);
        const blob = await TaskPoller.poll(task_id);
        window.clonePreviewUrl = URL.createObjectURL(blob);
        const container = document.getElementById('clone-preview-container');
        if (container) container.style.display = 'block';
        statusText.innerText = "Ready";
    } catch (e) { alert(e.message); }
    finally { if (btn) btn.disabled = false; }
}

export function playClonePreview() {
    if (window.clonePreviewUrl) {
        const player = document.getElementById('preview-player');
        player.src = window.clonePreviewUrl;
        player.play();
    }
}

export function saveClonedVoice() {
    const name = prompt("Voice Name:");
    if (!name || !state.voicelab.lastClonedPath) return;
    SpeakerStore.saveVoice({ id: Date.now(), name, type: 'clone', value: state.voicelab.lastClonedPath });
    renderVoiceLibrary();
    renderSpeechVoiceList();
}

export async function testVoiceMix(btn) { const type = 'voice_mix';
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
        TaskMonitor.addTask(task_id, type);
        const blob = await TaskPoller.poll(task_id);
        window.mixPreviewUrl = URL.createObjectURL(blob);
        state.voicelab.lastMixedPath = JSON.stringify(mixConfig);
        const container = document.getElementById('mix-preview-container');
        if (container) container.style.display = 'block';
        statusText.innerText = "Ready";
    } catch (e) { alert(e.message); }
    finally { if (btn) btn.disabled = false; }
}

export function playMixPreview() {
    if (window.mixPreviewUrl) {
        const player = document.getElementById('preview-player');
        player.src = window.mixPreviewUrl;
        player.play();
    }
}

export function saveMixedVoice() {
    const name = prompt("Voice Name:");
    if (!name || !state.voicelab.lastMixedPath) return;
    SpeakerStore.saveVoice({ id: Date.now(), name, type: 'mix', value: state.voicelab.lastMixedPath });
    renderVoiceLibrary();
    renderSpeechVoiceList();
}

export async function uploadVoiceImage(voiceId, file) {
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

export function deleteVoice(id) {
    if (confirm("Delete voice?")) { SpeakerStore.deleteVoice(id); renderVoiceLibrary(); renderSpeechVoiceList(); }
}

// --- Dubbing & S2S ---

export async function startDubbing() { const type = 'dubbing';
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
        TaskMonitor.addTask(task_id, type);
        const blob = await TaskPoller.poll(task_id, (task) => {
            statusText.innerText = `Dubbing: ${task.progress}%`;
        });

        const player = document.getElementById('main-audio-player');
        player.src = URL.createObjectURL(blob);
        player.play();
        statusText.innerText = "Dubbing Complete!";
    } catch (e) { alert(e.message); statusText.innerText = "Dubbing failed"; }
}

export async function startVoiceChanger() { const type = 'voice_changer';
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
        TaskMonitor.addTask(task_id, type);
        const blob = await TaskPoller.poll(task_id, (task) => {
            statusText.innerText = `Converting: ${task.progress}%`;
        });
        const player = document.getElementById('main-audio-player');
        player.src = URL.createObjectURL(blob);
        player.play();
        statusText.innerText = "Conversion Complete!";
    } catch (e) { alert(e.message); statusText.innerText = "Failed"; }
}
