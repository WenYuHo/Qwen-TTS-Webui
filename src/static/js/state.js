export const state = {
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

export const PRESETS = ["aiden", "dylan", "eric", "ono_anna", "ryan", "serena", "sohee", "uncle_fu", "vivian"];
