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
