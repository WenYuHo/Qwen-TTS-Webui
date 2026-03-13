// --- Qwen-TTS Studio Frontend (Main Entry) ---
import { TaskManager } from './task_manager.js';
import { AssetManager } from './assets.js';
import { SystemManager } from './system.js';
import { ProductionManager } from './production.js';
import { VoiceLabManager } from './voicelab.js';
import { DubbingManager } from './dubbing.js';
import { MetricsManager } from './metrics.js';
import { VideoModal, HelpManager } from './ui_components.js';

const state = {
    currentView: 'speech',
    whisper: false,
    rate: 'normal',
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

function setGlobalRate(rate) {
    state.rate = rate;
    document.querySelectorAll('.rate-btn').forEach(btn => {
        if (btn.dataset.rate === rate) {
            btn.classList.add('btn-primary');
            btn.classList.remove('btn-secondary');
        } else {
            btn.classList.add('btn-secondary');
            btn.classList.remove('btn-primary');
        }
    });
}
window.setGlobalRate = setGlobalRate;

// ⚡ Bolt: Global Background Services
setInterval(() => {
    // Global services
    TaskManager.refreshTasks();
    
    // View-specific services
    if (window.state && window.state.currentView === 'system') SystemManager.refreshResourceStats();
}, 2000);

function switchView(view) {
    console.log("switchView triggered for:", view);
    const currentViewEl = document.querySelector('.view-container.active');
    const targetViewEl = document.getElementById(`${view}-view`);
    
    if (!targetViewEl) {
        console.error("Target view element not found:", `${view}-view`);
        return;
    }

    if (currentViewEl && currentViewEl !== targetViewEl) {
        currentViewEl.classList.add('exiting');
        currentViewEl.classList.remove('active');
        
        setTimeout(() => {
            currentViewEl.classList.remove('exiting');
            performSwitch(view);
        }, 200); 
    } else {
        performSwitch(view);
    }
}

function performSwitch(view) {
    console.log("performSwitch execution for:", view);
    state.currentView = view;
    localStorage.setItem('studio_active_view', view);
    
    document.querySelectorAll('.view-container').forEach(v => {
        v.classList.remove('active');
        v.classList.remove('exiting');
    });
    
    document.querySelectorAll('.nav-item').forEach(v => {
        v.classList.remove('active');
        v.setAttribute('aria-pressed', 'false');
    });

    const targetView = document.getElementById(`${view}-view`);
    if (targetView) {
        targetView.classList.add('active');
        const heading = targetView.querySelector('h1') || targetView.querySelector('h2');
        if (heading) heading.focus();
    }

    const navBtn = document.getElementById(`nav-${view}`);
    if (navBtn) {
        navBtn.classList.add('active');
        navBtn.setAttribute('aria-pressed', 'true');
    }

    if (view === 'speech') {
        VoiceLabManager.loadVoiceLibrary();
        VoiceLabManager.setupCloningRecording();
    }
    if (view === 'assets') {
        AssetManager.loadAssets();
        AssetManager.setupDragAndDrop();
    }
    if (view === 'projects') {
        ProductionManager.fetchProjectList();
        ProductionManager.loadSubTabState();
        AssetManager.loadAssets(); // For BGM selection
    }
    if (view === 'system') {
        TaskManager.refreshTasks();
        SystemManager.fetchInventory();
        SystemManager.loadSystemSettings();
        SystemManager.loadSubTabState();
        SystemManager.refreshResourceStats();
    }
    if (view === 'dubbing') {
        DubbingManager.setupS2SRecording();
    }
}

// Global exposure
Object.assign(window, {
    switchView,
    startDubbing: DubbingManager.startDubbing.bind(DubbingManager),
    detectLanguage: DubbingManager.detectLanguage.bind(DubbingManager),
    syncPlayDub: DubbingManager.syncPlayDub.bind(DubbingManager),
    previewS2STarget: DubbingManager.previewS2STarget.bind(DubbingManager),
    uploadS2SFiles: DubbingManager.uploadS2SFiles.bind(DubbingManager),
    startVoiceChanger: DubbingManager.startVoiceChanger.bind(DubbingManager),
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
    getAllProfiles: VoiceLabManager.getAllProfiles.bind(VoiceLabManager),
    testVoiceDesign: VoiceLabManager.testVoiceDesign.bind(VoiceLabManager),
    testVoiceClone: VoiceLabManager.testVoiceClone.bind(VoiceLabManager),
    testVoiceMix: VoiceLabManager.testVoiceMix.bind(VoiceLabManager),
    filterVoiceLibrary: VoiceLabManager.filterVoiceLibrary.bind(VoiceLabManager),
    filterAssets: AssetManager.filterAssets.bind(AssetManager),
    filterProjects: ProductionManager.filterProjects.bind(ProductionManager),
    playDesignPreview: VoiceLabManager.playDesignPreview.bind(VoiceLabManager),
    playClonePreview: VoiceLabManager.playClonePreview.bind(VoiceLabManager),
    playMixPreview: VoiceLabManager.playMixPreview.bind(VoiceLabManager),
    saveDesignedVoice: () => {
        const name = prompt("Enter a name for this voice:");
        if (name) VoiceLabManager.saveVoice(name, { type: 'design', value: document.getElementById('design-prompt').value });
    },
    saveClonedVoice: () => {
        const name = prompt("Enter a name for this voice:");
        if (name) VoiceLabManager.saveVoice(name, { type: 'clone', value: window.state.voicelab.lastClonedPath });
    },
    saveMixedVoice: async () => {
        const name = prompt("Enter a name for this voice:");
        if (name) {
            const vA = document.getElementById('mix-voice-a').value;
            const vB = document.getElementById('mix-voice-b').value;
            const wA = parseInt(document.getElementById('mix-weight-a').value || 50) / 100;
            const wB = parseInt(document.getElementById('mix-weight-b').value || 50) / 100;
            
            const allProfiles = await VoiceLabManager.getAllProfiles();
            const mixConfig = [
                { profile: allProfiles[vA], weight: wA },
                { profile: allProfiles[vB], weight: wB }
            ];
            VoiceLabManager.saveVoice(name, { type: 'mix', value: JSON.stringify(mixConfig) });
        }
    },
    saveVoice: VoiceLabManager.saveVoice.bind(VoiceLabManager),
    previewVoice: VoiceLabManager.previewVoice.bind(VoiceLabManager),
    deleteVoice: VoiceLabManager.deleteVoice.bind(VoiceLabManager),
    addPhonemeOverride: SystemManager.addPhonemeOverride.bind(SystemManager),
    removePhonemeOverride: SystemManager.removePhonemeOverride.bind(SystemManager),
    importPhonemes: SystemManager.importPhonemes.bind(SystemManager),
    updateWatermarkSettings: SystemManager.updateWatermarkSettings.bind(SystemManager),
    fetchAuditLog: SystemManager.fetchAuditLog.bind(SystemManager),
    refreshResourceStats: SystemManager.refreshResourceStats.bind(SystemManager),
    switchSystemSubTab: SystemManager.switchSystemSubTab.bind(SystemManager),
    loadSubTabState: SystemManager.loadSubTabState.bind(SystemManager),
    clearCache: SystemManager.clearCache.bind(SystemManager),
    runEngineBenchmark: SystemManager.runEngineBenchmark.bind(SystemManager),
    loadProject: ProductionManager.loadProject.bind(ProductionManager),
    saveProject: ProductionManager.saveProject.bind(ProductionManager),
    toggleCanvasView: ProductionManager.toggleCanvasView.bind(ProductionManager),
    promoteToProduction: ProductionManager.promoteToProduction.bind(ProductionManager),
    showVideoPreview: VideoModal.show.bind(VideoModal),
    hideVideoModal: VideoModal.hide.bind(VideoModal),
    showHelp: () => HelpManager.show(state.currentView),
    setupDragAndDrop: AssetManager.setupDragAndDrop,
    applyAccent: SystemManager.applyAccent.bind(SystemManager),
    
    playTaskResult: (taskId) => {
        const player = document.getElementById('preview-player');
        if (player) {
            player.src = `/api/tasks/${taskId}/result`;
            player.play();
        }
    },
    
    shareCurrentAudio: () => {
        const player = document.getElementById('preview-player');
        if (!player || !player.src || player.src === window.location.href) {
            return Notification.show("Nothing playing to share", "warn");
        }
        
        // In a real app, this would be a public cloud URL
        const mockUrl = `https://studio.qwen-tts.ai/share/${Math.random().toString(36).substring(7)}`;
        navigator.clipboard.writeText(mockUrl).then(() => {
            Notification.show("Share link copied to clipboard!", "success");
        });
    }
});

document.addEventListener('DOMContentLoaded', async () => {
    SystemManager.loadTheme();
    VoiceLabManager.loadVoiceLibrary();
    SystemManager.fetchInventory();
    UIHeartbeat.start();
    MetricsManager.start();
    CanvasManager.load();
    HelpManager.checkFirstRun();

    // Multilingual Initialization
    await window.loadLanguages();
    window.populateLanguageDropdown('preview-language', true);
    window.populateLanguageDropdown('dub-lang', false);

    const savedView = localStorage.getItem('studio_active_view');
    if (savedView && savedView !== 'speech') {
        performSwitch(savedView);
    }

    // Keyboard shortcuts for Undo/Redo
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
            e.preventDefault();
            window.CanvasManager.undo();
        } else if (e.ctrlKey && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
            e.preventDefault();
            window.CanvasManager.redo();
        }
    });
});
