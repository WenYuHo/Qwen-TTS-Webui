// --- Qwen-TTS Studio Frontend (Main Entry) ---
import { TaskManager } from './task_manager.js';
import { AssetManager } from './assets.js';
import { SystemManager } from './system.js';
import { ProductionManager } from './production.js';
import { VoiceLabManager } from './voicelab.js';

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
window.state = state;

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
        AssetManager.loadAssets();
        AssetManager.setupDragAndDrop();
    }
    if (view === 'system') {
        TaskManager.refreshTasks();
        SystemManager.fetchInventory();
        SystemManager.loadSystemSettings();
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
        TaskManager.pollTask(data.task_id, async (taskData) => {
            const audioRes = await fetch(`/api/tasks/${data.task_id}/result`);
            const blob = await audioRes.blob();
            const url = URL.createObjectURL(blob);
            const player = document.getElementById('main-audio-player');
            if (player) {
                player.src = url;
                player.play();
            }
            alert("Dubbing Complete!");
        });
    } catch (err) {
        if (statusText) statusText.innerText = "Dubbing Error";
        console.error(err);
    }
}

// Global exposure for legacy HTML event handlers
Object.assign(window, {
    switchView,
    startDubbing,
    loadAssets: AssetManager.loadAssets,
    uploadAsset: AssetManager.uploadAsset,
    deleteAsset: AssetManager.deleteAsset,
    playAsset: AssetManager.playAsset,
    refreshTasks: TaskManager.refreshTasks,
    cancelTask: TaskManager.cancelTask,
    clearCompletedTasks: TaskManager.clearCompletedTasks,
    exportStudioBundle: ProductionManager.exportStudioBundle,
    generatePodcast: ProductionManager.generatePodcast,
    suggestVideoScene: ProductionManager.suggestVideoScene.bind(ProductionManager),
    triggerDownload: SystemManager.triggerDownload,
    testVoiceDesign: VoiceLabManager.testVoiceDesign.bind(VoiceLabManager),
    testVoiceClone: VoiceLabManager.testVoiceClone.bind(VoiceLabManager),
    testVoiceMix: VoiceLabManager.testVoiceMix.bind(VoiceLabManager),
    playDesignPreview: VoiceLabManager.playDesignPreview.bind(VoiceLabManager),
    playClonePreview: VoiceLabManager.playClonePreview.bind(VoiceLabManager),
    playMixPreview: VoiceLabManager.playMixPreview.bind(VoiceLabManager),
    addPhonemeOverride: SystemManager.addPhonemeOverride.bind(SystemManager),
    removePhonemeOverride: SystemManager.removePhonemeOverride.bind(SystemManager),
    importPhonemes: SystemManager.importPhonemes.bind(SystemManager),
    updateWatermarkSettings: SystemManager.updateWatermarkSettings.bind(SystemManager),
    setupDragAndDrop: AssetManager.setupDragAndDrop
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setInterval(() => {
        if (['projects', 'dubbing', 'system'].includes(state.currentView)) TaskManager.refreshTasks();
    }, 5000);
});
