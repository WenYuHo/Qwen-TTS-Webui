// --- Dubbing & S2S Module ---
import { Notification, ErrorDisplay } from './ui_components.js';
import { TaskManager } from './task_manager.js';

export const DubbingManager = {
    async startDubbing() {
        const fileInput = document.getElementById('dub-file');
        const targetLang = document.getElementById('dub-lang').value;
        
        if (!fileInput.files.length) return Notification.show("Select a file to dub", "warn");
        
        Notification.show("Uploading source file...", "info");
        
        try {
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            const upRes = await fetch('/api/voice/upload', { method: 'POST', body: formData });
            const upData = await upRes.json();
            
            if (upData.error) throw new Error(upData.error);
            
            const dubRes = await fetch('/api/dub/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    input_file: upData.filename,
                    target_lang: targetLang
                })
            });
            
            const dubData = await dubRes.json();
            if (dubData.error) throw new Error(dubData.error);
            
            Notification.show("Dubbing task created", "success");
            if (window.refreshTasks) window.refreshTasks();
            
        } catch (err) {
            ErrorDisplay.show("Dubbing Failed", err.message);
        }
    },

    async startVoiceChanger() {
        const targetVoice = document.getElementById('s2s-target-voice').value;
        const preserveProsody = document.getElementById('s2s-preserve').checked;
        const sourcePath = window.state.s2s.lastUploadedPath;
        
        if (!sourcePath) return Notification.show("Record or upload source audio", "warn");
        if (!targetVoice) return Notification.show("Select a target voice", "warn");
        
        try {
            const res = await fetch('/api/s2s/convert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_wav_path: sourcePath,
                    target_voice_id: targetVoice,
                    preserve_prosody: preserveProsody
                })
            });
            
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            
            Notification.show("Voice conversion task created", "success");
            if (window.refreshTasks) window.refreshTasks();
            
        } catch (err) {
            ErrorDisplay.show("S2S Failed", err.message);
        }
    },

    setupS2SRecording() {
        const btn = document.getElementById('s2s-record-btn');
        if (!btn) return;

        btn.onclick = async () => {
            if (!window.state.s2s.isRecording) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    window.state.s2s.mediaRecorder = new MediaRecorder(stream);
                    window.state.s2s.audioChunks = [];

                    window.state.s2s.mediaRecorder.ondataavailable = (event) => {
                        window.state.s2s.audioChunks.push(event.data);
                    };

                    window.state.s2s.mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(window.state.s2s.audioChunks, { type: 'audio/wav' });
                        const formData = new FormData();
                        formData.append('file', audioBlob, 's2s_input.wav');
                        
                        Notification.show("Uploading recording...", "info");
                        const upRes = await fetch('/api/voice/upload', { method: 'POST', body: formData });
                        const upData = await upRes.json();
                        window.state.s2s.lastUploadedPath = upData.filename;
                        Notification.show("Recording ready for S2S", "success");
                    };

                    window.state.s2s.mediaRecorder.start();
                    window.state.s2s.isRecording = true;
                    btn.innerHTML = '<i class="fas fa-stop"></i> STOP RECORDING';
                    btn.classList.add('btn-danger');
                } catch (err) {
                    Notification.show("Microphone access denied", "error");
                }
            } else {
                window.state.s2s.mediaRecorder.stop();
                window.state.s2s.isRecording = false;
                btn.innerHTML = '<i class="fas fa-circle"></i> RECORD AUDIO';
                btn.classList.remove('btn-danger');
            }
        };
    }
};
