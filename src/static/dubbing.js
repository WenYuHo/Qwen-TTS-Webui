// --- Dubbing & S2S Module ---
import { Notification, ErrorDisplay } from './ui_components.js';
import { TaskManager } from './task_manager.js';

export const DubbingManager = {
    wavesurfer: null,

    async startDubbing(btn) {
        const fileInput = document.getElementById('dub-file');
        const targetLang = document.getElementById('dub-lang').value;
        
        if (!fileInput.files.length && !window.state.dubbing?.lastUploadedPath) return Notification.show("Select a file to dub", "warn");
        
        btn.disabled = true;
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> PROCESSING...';

        try {
            let filename = window.state.dubbing?.lastUploadedPath;
            
            if (fileInput.files.length) {
                Notification.show("Uploading source file...", "info");
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                const upRes = await fetch('/api/voice/upload', { method: 'POST', body: formData });
                const upData = await upRes.json();
                if (upData.error) throw new Error(upData.error);
                filename = upData.filename;
                window.state.dubbing = { lastUploadedPath: filename };
                this.initDubPreview(filename);
            }
            
            const dubRes = await fetch('/api/generate/dub', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_audio: filename,
                    target_lang: targetLang
                })
            });
            
            const dubData = await dubRes.json();
            if (dubData.error) throw new Error(dubData.error);
            
            Notification.show("Dubbing task created", "success");
            
            TaskManager.pollTask(dubData.task_id, (task) => {
                Notification.show("Dubbing Complete!", "success");
                this.showComparison(filename, task.id);
            });
            
        } catch (err) {
            ErrorDisplay.show("Dubbing Failed", err.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    },

    showComparison(originalFile, taskId) {
        const container = document.getElementById('dub-comparison');
        container.style.display = 'block';

        const origPlayer = document.getElementById('dub-comp-original');
        const dubbedPlayer = document.getElementById('dub-comp-dubbed');

        origPlayer.src = `/api/voice/uploads/${originalFile}`;
        dubbedPlayer.src = `/api/tasks/${taskId}/result`;

        // Add subtitle download links
        let links = container.querySelector('.dub-subtitle-links');
        if (!links) {
            links = document.createElement('div');
            links.className = 'dub-subtitle-links';
            links.style.marginTop = '12px';
            links.style.display = 'flex';
            links.style.gap = '8px';
            container.appendChild(links);
        }
        links.innerHTML = `
            <a href="/api/generate/dub/${taskId}/subtitles?format=srt" download="subtitles.srt" class="btn btn-secondary btn-sm" style="flex:1; font-size:0.6rem;">📥 SRT SUBS</a>
            <a href="/api/generate/dub/${taskId}/subtitles?format=vtt" download="subtitles.vtt" class="btn btn-secondary btn-sm" style="flex:1; font-size:0.6rem;">📥 VTT SUBS</a>
        `;
    },

    syncPlayDub() {
        const orig = document.getElementById('dub-comp-original');
        const dubbed = document.getElementById('dub-comp-dubbed');
        
        orig.currentTime = 0;
        dubbed.currentTime = 0;
        orig.play();
        dubbed.play();
    },

    initDubPreview(filename) {
        const container = document.getElementById('dub-source-preview');
        container.style.display = 'block';

        if (this.wavesurfer) {
            this.wavesurfer.destroy();
        }

        const audioUrl = `/api/voice/uploads/${filename}`;
        
        this.wavesurfer = WaveSurfer.create({
            container: '#dub-ws-container',
            waveColor: '#ccff00',
            progressColor: '#555',
            cursorColor: '#ccff00',
            barWidth: 2,
            barRadius: 3,
            cursorWidth: 1,
            height: 64,
            responsive: true,
            normalize: true,
            partialRender: true
        });

        this.wavesurfer.load(audioUrl);

        const playBtn = document.getElementById('dub-preview-play-btn');
        const timeEl = document.getElementById('dub-preview-time');

        this.wavesurfer.on('ready', () => {
            const duration = this.formatTime(this.wavesurfer.getDuration());
            timeEl.innerText = `00:00 / ${duration}`;
        });

        this.wavesurfer.on('audioprocess', () => {
            const current = this.formatTime(this.wavesurfer.getCurrentTime());
            const duration = this.formatTime(this.wavesurfer.getDuration());
            timeEl.innerText = `${current} / ${duration}`;
        });

        playBtn.onclick = () => {
            this.wavesurfer.playPause();
            const isPlaying = this.wavesurfer.isPlaying();
            playBtn.innerHTML = isPlaying ? '<i class="fas fa-pause" aria-hidden="true"></i>' : '<i class="fas fa-play" aria-hidden="true"></i>';
            playBtn.setAttribute('aria-label', isPlaying ? 'Pause source audio' : 'Play source audio');
            playBtn.setAttribute('title', isPlaying ? 'Pause source audio' : 'Play source audio');
        };

        this.wavesurfer.on('finish', () => {
            playBtn.innerHTML = '<i class="fas fa-play" aria-hidden="true"></i>';
            playBtn.setAttribute('aria-label', 'Play source audio');
            playBtn.setAttribute('title', 'Play source audio');
        });
    },

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        seconds = Math.floor(seconds % 60);
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    },

    async detectLanguage(btn) {
        const fileInput = document.getElementById('dub-file');
        if (!fileInput.files.length && !window.state.dubbing?.lastUploadedPath) return Notification.show("Select a file first", "warn");

        btn.disabled = true;
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            let filename = window.state.dubbing?.lastUploadedPath;
            if (fileInput.files.length) {
                Notification.show("Uploading for detection...", "info");
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                const upRes = await fetch('/api/voice/upload', { method: 'POST', body: formData });
                const upData = await upRes.json();
                filename = upData.filename;
                window.state.dubbing = { lastUploadedPath: filename };
                this.initDubPreview(filename);
            }

            const res = await fetch('/api/generate/detect-language', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source_audio: filename })
            });
            const data = await res.json();
            if (data.error) throw new Error(data.error);

            Notification.show(`Detected Language: ${data.language.toUpperCase()}`, "success");
            const langSelect = document.getElementById('dub-lang');
            // Try to auto-select if it exists in options
            for (let opt of langSelect.options) {
                if (opt.value === data.language) {
                    langSelect.value = data.language;
                    break;
                }
            }
        } catch (err) {
            Notification.show("Detection Failed: " + err.message, "error");
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    },

    async previewS2STarget(btn) {
        const targetVoiceId = document.getElementById('s2s-target-voice').value;
        if (!targetVoiceId) return Notification.show("Select a target voice", "warn");

        btn.disabled = true;
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const allProfiles = await window.getAllProfiles();
            const profile = allProfiles[targetVoiceId];
            await window.previewVoice(profile.type, profile.value);
        } catch (err) {
            Notification.show("Preview failed: " + err.message, "error");
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    },

    async startVoiceChanger(btn) {
        const targetVoiceId = document.getElementById('s2s-target-voice').value;
        const preserveProsody = document.getElementById('s2s-preserve').checked;
        const emotion = document.getElementById('s2s-emotion').value;
        const sourcePaths = window.state.s2s.lastUploadedPaths || (window.state.s2s.lastUploadedPath ? [window.state.s2s.lastUploadedPath] : []);
        
        if (sourcePaths.length === 0) return Notification.show("Record or upload source audio", "warn");
        if (!targetVoiceId) return Notification.show("Select a target voice", "warn");
        
        btn.disabled = true;
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> PROCESSING...';

        try {
            const allProfiles = await window.getAllProfiles();
            const targetProfile = allProfiles[targetVoiceId];

            const endpoint = sourcePaths.length > 1 ? '/api/generate/s2s/batch' : '/api/generate/s2s';
            const body = sourcePaths.length > 1 
                ? { source_audios: sourcePaths, target_voice: targetProfile, preserve_prosody: preserveProsody, instruct: emotion || null }
                : { source_audio: sourcePaths[0], target_voice: targetProfile, preserve_prosody: preserveProsody, instruct: emotion || null };

            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            
            Notification.show(sourcePaths.length > 1 ? "Batch S2S task created" : "Voice conversion task created", "success");
            if (window.refreshTasks) window.refreshTasks();
            
        } catch (err) {
            ErrorDisplay.show("S2S Failed", err.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    },

    async uploadS2SFiles(input) {
        if (!input.files.length) return;
        
        const listEl = document.getElementById('s2s-file-list');
        listEl.innerText = "Uploading...";
        
        const paths = [];
        try {
            for (let file of input.files) {
                const formData = new FormData();
                formData.append('file', file);
                const res = await fetch('/api/voice/upload', { method: 'POST', body: formData });
                const data = await res.json();
                paths.push(data.filename);
            }
            window.state.s2s.lastUploadedPaths = paths;
            window.state.s2s.lastUploadedPath = paths[0]; // Compatibility for single
            listEl.innerText = `${paths.length} file(s) ready`;
            Notification.show(`${paths.length} files uploaded for S2S`, "success");
        } catch (err) {
            listEl.innerText = "Upload failed";
            Notification.show("Upload failed: " + err.message, "error");
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
                    btn.innerHTML = '<i class="fas fa-stop" aria-hidden="true"></i> STOP RECORDING';
                    btn.setAttribute('aria-label', 'Stop recording');
                    btn.setAttribute('title', 'Stop recording');
                    btn.classList.add('btn-danger');
                } catch (err) {
                    Notification.show("Microphone access denied", "error");
                }
            } else {
                window.state.s2s.mediaRecorder.stop();
                window.state.s2s.isRecording = false;
                btn.innerHTML = '<i class="fas fa-circle" aria-hidden="true"></i> RECORD AUDIO';
                btn.setAttribute('aria-label', 'Record source audio');
                btn.setAttribute('title', 'Record source audio');
                btn.classList.remove('btn-danger');
            }
        };
    }
};
