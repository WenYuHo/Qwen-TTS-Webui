// --- Voice Lab (Design, Clone, Mix) Module ---
import { TaskManager } from './task_manager.js';
import { Notification, ErrorDisplay } from './ui_components.js';

export const VoiceLabManager = {
    async testVoiceDesign(btn) {
        const promptText = document.getElementById('design-prompt').value;
        const stabilityBoost = document.getElementById('stability-boost').checked;
        if (!promptText) return Notification.show("Enter a style prompt", "warn");

        const container = document.getElementById('design-preview-container');
        const status = document.getElementById('design-status');

        if (container) container.style.display = 'block';
        if (status) status.innerText = "Designing...";

        btn.disabled = true;
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> DESIGNING...';

        try {
            const customText = document.getElementById('custom-preview-text')?.value?.trim() || '';
            let finalPrompt = promptText;
            if (stabilityBoost) {
                finalPrompt = `${promptText}, stable delivery, clear speech, consistent tone, no distortion`;
            }

            const profile = { type: 'design', value: finalPrompt };

            // ⚡ Bolt: Use Task-based generation for background processing
            const res = await fetch('/api/generate/segment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    profiles: [{ role: 'preview', ...profile }],
                    script: [{ role: 'preview', text: customText || "Yesterday's weather was absolutely perfect — warm sunshine, cool breezes, and a beautiful golden sunset over the mountains." }]
                })
            });

            if (!res.ok) throw new Error("Design task creation failed");
            const { task_id } = await res.json();

            status.innerText = "Processing...";
            Notification.show("Voice design started in background", "info");

            TaskManager.pollTask(task_id, (data) => {
                const blob = new Blob([new Uint8Array(data.result)], { type: 'audio/wav' });
                const url = URL.createObjectURL(blob);
                window.state.voicelab.lastDesignedPath = url;

                const player = document.getElementById('preview-player');
                if (player) {
                    player.src = url;
                    player.play();
                }
                status.innerText = "Ready";
                btn.disabled = false;
                btn.innerHTML = originalHtml;
                Notification.show("Design preview ready", "success");
            });

        } catch (err) {
            if (status) status.innerText = "Error";
            ErrorDisplay.show("Design Error", err.message);
            console.error(err);
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    },

    async testVoiceClone(btn) {
        const fileInput = document.getElementById('clone-file');
        if (!window.state.voicelab.lastClonedPath && !fileInput.files.length) {
            return Notification.show("Reference audio required", "warn");
        }

        const container = document.getElementById('clone-preview-container');
        const status = document.getElementById('clone-status');

        if (container) container.style.display = 'block';
        if (status) status.innerText = "Cloning...";

        btn.disabled = true;
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> CLONING...';

        try {
            let path = window.state.voicelab.lastClonedPath;
            if (fileInput.files.length > 0) {
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                const upRes = await fetch('/api/voice/upload', { method: 'POST', body: formData });
                const upData = await upRes.json();
                path = upData.filename;
                window.state.voicelab.lastClonedPath = path;
            }

            const customText = document.getElementById('custom-preview-text')?.value?.trim() || '';
            const refText = document.getElementById('clone-ref-text')?.value?.trim() || '';
            const profile = { type: 'clone', value: path };
            // Pass ref_text for ICL mode — dramatically improves cloning quality
            if (refText) profile.ref_text = refText;
            const res = await fetch('/api/generate/segment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    profiles: [{ role: 'preview', ...profile }],
                    script: [{ role: 'preview', text: customText || "She whispered softly, 'Don't worry, everything will be alright,' then smiled with quiet confidence." }]
                })
            });

            if (!res.ok) throw new Error("Clone task creation failed");
            const { task_id } = await res.json();

            status.innerText = "Cloning...";
            Notification.show("Voice cloning started in background", "info");

            TaskManager.pollTask(task_id, (data) => {
                const blob = new Blob([new Uint8Array(data.result)], { type: 'audio/wav' });
                const url = URL.createObjectURL(blob);

                const player = document.getElementById('preview-player');
                if (player) {
                    player.src = url;
                    player.play();
                }
                status.innerText = "Ready";
                btn.disabled = false;
                btn.innerHTML = originalHtml;
                Notification.show("Clone preview ready", "success");
            });

        } catch (err) {
            if (status) status.innerText = "Error";
            ErrorDisplay.show("Cloning Error", err.message);
            console.error(err);
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    },

    async testVoiceMix(btn) {
        const vA = document.getElementById('mix-voice-a').value;
        const vB = document.getElementById('mix-voice-b').value;
        const wA = parseInt(document.getElementById('mix-weight-a').value || 50) / 100;
        const wB = parseInt(document.getElementById('mix-weight-b').value || 50) / 100;

        if (!vA || !vB) return Notification.show("Select two voices to mix", "warn");

        const container = document.getElementById('mix-preview-container');
        const status = document.getElementById('mix-status');

        if (container) container.style.display = 'block';
        if (status) status.innerText = "Mixing...";

        btn.disabled = true;
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> MIXING...';

        try {
            const profiles = await this.getAllProfiles();
            const mixConfig = [
                { profile: profiles[vA], weight: wA },
                { profile: profiles[vB], weight: wB }
            ];
            const profile = { type: 'mix', value: JSON.stringify(mixConfig) };

            const res = await fetch('/api/generate/segment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    profiles: [{ role: 'preview', ...profile }],
                    script: [{ role: 'preview', text: (document.getElementById('custom-preview-text')?.value?.trim()) || "From quantum physics to classical music, the breadth of human knowledge never ceases to amaze me." }]
                })
            });

            if (!res.ok) throw new Error("Mix task creation failed");
            const { task_id } = await res.json();

            status.innerText = "Mixing...";
            Notification.show("Voice mixing started in background", "info");

            TaskManager.pollTask(task_id, (data) => {
                const blob = new Blob([new Uint8Array(data.result)], { type: 'audio/wav' });
                const url = URL.createObjectURL(blob);
                window.state.voicelab.lastMixedPath = url;

                const player = document.getElementById('preview-player');
                if (player) {
                    player.src = url;
                    player.play();
                }
                status.innerText = "Ready";
                btn.disabled = false;
                btn.innerHTML = originalHtml;
                Notification.show("Mix preview ready", "success");
            });

        } catch (err) {
            if (status) status.innerText = "Error";
            btn.disabled = false;
            btn.innerHTML = originalHtml;
            ErrorDisplay.show("Mixing Error", err.message);
            console.error(err);
        }
    },

    async loadVoiceLibrary() {
        try {
            const [libRes, speakerRes] = await Promise.all([
                fetch('/api/voice/library'),
                fetch('/api/voice/speakers')
            ]);
            const libData = await libRes.json();
            const speakerData = await speakerRes.json();

            this.renderVoiceLibrary(libData.voices, speakerData.presets);
            this.updateMixDropdowns(libData.voices, speakerData.presets);
        } catch (err) { console.error("Failed to load voices", err); }
    },

    renderVoiceLibrary(savedVoices, presets) {
        const grid = document.getElementById('voice-library-grid');
        if (!grid) return;

        // ⚡ Bolt: Enhanced Preset Cards with Metadata
        let html = presets.map(p => {
            const name = typeof p === 'string' ? p : p.name;
            const id = typeof p === 'string' ? p : p.id;
            const meta = typeof p === 'string' ? 'PRESET VOICE' : `${p.gender} | ${p.description}`;

            return `
            <div class="card voice-card" style="padding:16px; border-left:4px solid var(--accent);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="text-transform:uppercase;">${name}</strong>
                        <div style="font-size:0.7rem; opacity:0.7;">${meta}</div>
                    </div>
                    <button class="btn btn-secondary btn-sm" onclick="previewVoice(this, 'preset', '${id}')" title="Preview ${name}" aria-label="Preview ${name}"><i class="fas fa-play" aria-hidden="true"></i></button>
                </div>
            </div>`;
        }).join('');

        html += savedVoices.map(v => `
            <div class="card voice-card" style="padding:16px; border-left:4px solid var(--text-primary);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="text-transform:uppercase;">${v.name}</strong>
                        <div style="font-size:0.7rem; opacity:0.5;">${v.profile.type.toUpperCase()}</div>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-secondary btn-sm" onclick="previewVoice(this, '${v.profile.type}', '${v.profile.value}')" title="Preview ${v.name}" aria-label="Preview ${v.name}"><i class="fas fa-play" aria-hidden="true"></i></button>
                        <button class="btn btn-danger btn-sm" onclick="deleteVoice('${v.name}')" style="padding:4px 8px;" title="Delete ${v.name}" aria-label="Delete ${v.name}"><i class="fas fa-trash" aria-hidden="true"></i></button>
                    </div>
                </div>
            </div>
        `).join('');

        grid.innerHTML = html;
    },

    updateMixDropdowns(savedVoices, presets) {
        const a = document.getElementById('mix-voice-a');
        const b = document.getElementById('mix-voice-b');
        const s2s = document.getElementById('s2s-target-voice');
        if (!a || !b) return;

        const options = [
            ...presets.map(p => {
                const name = typeof p === 'string' ? p : p.name;
                const id = typeof p === 'string' ? p : p.id;
                return `<option value="${id}">${name} (Preset)</option>`;
            }),
            ...savedVoices.map(v => `<option value="${v.name}">${v.name} (${v.profile.type})</option>`)
        ].join('');

        a.innerHTML = options;
        b.innerHTML = options;
        if (s2s) s2s.innerHTML = options;
    },

    async getAllProfiles() {
        const [libRes, speakerRes] = await Promise.all([
            fetch('/api/voice/library'),
            fetch('/api/voice/speakers')
        ]);
        const libData = await libRes.json();
        const speakerData = await speakerRes.json();

        const profiles = {};
        speakerData.presets.forEach(p => {
            const id = typeof p === 'string' ? p : p.id;
            profiles[id] = { type: 'preset', value: id };
        });
        libData.voices.forEach(v => profiles[v.name] = v.profile);
        return profiles;
    },

    async saveVoice(name, profile) {
        try {
            const res = await fetch('/api/voice/library');
            const data = await res.json();
            data.voices.push({ name, profile });

            await fetch('/api/voice/library', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            Notification.show("Voice saved to library", "success");
            this.loadVoiceLibrary();
        } catch (err) { Notification.show("Failed to save voice", "error"); }
    },

    async deleteVoice(name) {
        if (!confirm(`Delete voice "${name}"?`)) return;
        try {
            const res = await fetch('/api/voice/library');
            const data = await res.json();
            data.voices = data.voices.filter(v => v.name !== name);

            await fetch('/api/voice/library', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            this.loadVoiceLibrary();
        } catch (err) { console.error(err); }
    },

    async previewVoice(btn, type, value) {
        const player = document.getElementById('preview-player');
        const customText = document.getElementById('custom-preview-text')?.value?.trim() || '';

        // Loading state
        btn.disabled = true;
        btn.dataset.original = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const body = { type, value, name: "Preview" };
            if (customText) body.preview_text = customText;
            const res = await fetch('/api/voice/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const blob = await res.blob();
            player.src = URL.createObjectURL(blob);
            player.play();
        } catch (err) {
            console.error(err);
            Notification.show("Preview failed", "error");
        } finally {
            btn.disabled = false;
            btn.innerHTML = btn.dataset.original;
        }
    },

    playDesignPreview() {
        const player = document.getElementById('preview-player');
        if (window.state.voicelab.lastDesignedPath) {
            player.src = window.state.voicelab.lastDesignedPath;
            player.play();
        }
    },

    playClonePreview() {
        const player = document.getElementById('preview-player');
        if (window.state.voicelab.lastClonedPath) {
            player.src = window.state.voicelab.lastClonedPath;
            player.play();
        }
    },

    playMixPreview() {
        const player = document.getElementById('preview-player');
        if (window.state.voicelab.lastMixedPath) {
            player.src = window.state.voicelab.lastMixedPath;
            player.play();
        }
    },

    filterVoiceLibrary() {
        const query = document.getElementById('voice-search').value.toLowerCase();
        const cards = document.querySelectorAll('#voice-library-grid .voice-card');
        cards.forEach(card => {
            const name = card.querySelector('strong')?.innerText.toLowerCase() || '';
            card.style.display = name.includes(query) ? 'flex' : 'none';
        });
    },

    setupCloningRecording() {
        const btn = document.getElementById('clone-record-btn');
        if (!btn) return;

        btn.onclick = async () => {
            if (!window.state.voicelab.isRecording) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    window.state.voicelab.mediaRecorder = new MediaRecorder(stream);
                    window.state.voicelab.audioChunks = [];

                    window.state.voicelab.mediaRecorder.ondataavailable = (event) => {
                        window.state.voicelab.audioChunks.push(event.data);
                    };

                    window.state.voicelab.mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(window.state.voicelab.audioChunks, { type: 'audio/wav' });
                        const formData = new FormData();
                        formData.append('file', audioBlob, 'clone_input.wav');

                        Notification.show("Uploading recording...", "info");
                        const upRes = await fetch('/api/voice/upload', { method: 'POST', body: formData });
                        const upData = await upRes.json();
                        window.state.voicelab.lastClonedPath = upData.filename;
                        Notification.show("Recording ready for cloning", "success");
                    };

                    window.state.voicelab.mediaRecorder.start();
                    window.state.voicelab.isRecording = true;
                    btn.innerHTML = 'STOP';
                    btn.classList.remove('btn-danger');
                    btn.classList.add('btn-secondary');
                } catch (err) {
                    Notification.show("Microphone access denied", "error");
                }
            } else {
                window.state.voicelab.mediaRecorder.stop();
                window.state.voicelab.isRecording = false;
                btn.innerHTML = 'RECORD';
                btn.classList.remove('btn-secondary');
                btn.classList.add('btn-danger');
            }
        };
    }
};
