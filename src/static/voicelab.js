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
        const player = document.getElementById('preview-player');

        if (container) container.style.display = 'block';
        if (status) status.innerText = "Designing...";
        btn.disabled = true;

        try {
            let finalPrompt = promptText;
            if (stabilityBoost) {
                finalPrompt = `${promptText}, stable delivery, clear speech, consistent tone, no distortion`;
            }

            const profile = { type: 'design', value: finalPrompt };
            const res = await fetch('/api/generate/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    text: "This is a preview of the voice you designed. It should sound consistent from start to finish.", 
                    profile: profile 
                })
            });

            if (!res.ok) throw new Error("Design preview failed");

            const reader = res.body.getReader();
            const chunks = [];
            while(true) {
                const {done, value} = await reader.read();
                if (done) break;
                chunks.push(value);
                if (chunks.length === 1) {
                    const blob = new Blob([value], { type: 'audio/wav' });
                    player.src = URL.createObjectURL(blob);
                    player.play();
                }
            }
            const fullBlob = new Blob(chunks, { type: 'audio/wav' });
            window.state.voicelab.lastDesignedPath = URL.createObjectURL(fullBlob);
            status.innerText = "Ready";
            Notification.show("Design preview ready", "success");
        } catch (err) {
            status.innerText = "Error";
            ErrorDisplay.show("Design Error", err.message);
            console.error(err);
        } finally {
            btn.disabled = false;
        }
    },

    async testVoiceClone(btn) {
        const fileInput = document.getElementById('clone-file');
        if (!window.state.voicelab.lastClonedPath && !fileInput.files.length) {
            return Notification.show("Reference audio required", "warn");
        }

        const container = document.getElementById('clone-preview-container');
        const status = document.getElementById('clone-status');
        const player = document.getElementById('preview-player');

        container.style.display = 'block';
        status.innerText = "Cloning...";
        btn.disabled = true;

        try {
            let path = window.state.voicelab.lastClonedPath;
            if (fileInput.files.length > 0) {
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                const upRes = await fetch('/api/voice/upload', { method: 'POST', body: formData });
                const upData = await upRes.json();
                path = upData.filename;
            }

            const profile = { type: 'clone', value: path };
            const res = await fetch('/api/generate/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: "This is a preview of your cloned voice.", profile: profile })
            });

            if (!res.ok) throw new Error("Clone preview failed");

            const reader = res.body.getReader();
            const chunks = [];
            while(true) {
                const {done, value} = await reader.read();
                if (done) break;
                chunks.push(value);
                if (chunks.length === 1) {
                    const blob = new Blob([value], { type: 'audio/wav' });
                    player.src = URL.createObjectURL(blob);
                    player.play();
                }
            }
            const fullBlob = new Blob(chunks, { type: 'audio/wav' });
            window.state.voicelab.lastClonedPath = URL.createObjectURL(fullBlob);
            status.innerText = "Ready";
            Notification.show("Clone preview ready", "success");
        } catch (err) {
            status.innerText = "Error";
            ErrorDisplay.show("Cloning Error", err.message);
            console.error(err);
        } finally {
            btn.disabled = false;
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
        const player = document.getElementById('preview-player');

        if (container) container.style.display = 'block';
        if (status) status.innerText = "Mixing...";
        btn.disabled = true;

        try {
            const profiles = await this.getAllProfiles();
            const mixConfig = [
                { profile: profiles[vA], weight: wA },
                { profile: profiles[vB], weight: wB }
            ];
            const profile = { type: 'mix', value: JSON.stringify(mixConfig) };

            const res = await fetch('/api/generate/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: "This is a preview of your mixed voice.", profile: profile })
            });

            if (!res.ok) throw new Error("Mix preview failed");

            const reader = res.body.getReader();
            const chunks = [];
            while(true) {
                const {done, value} = await reader.read();
                if (done) break;
                chunks.push(value);
                if (chunks.length === 1) {
                    const blob = new Blob([value], { type: 'audio/wav' });
                    player.src = URL.createObjectURL(blob);
                    player.play();
                }
            }
            const fullBlob = new Blob(chunks, { type: 'audio/wav' });
            window.state.voicelab.lastMixedPath = URL.createObjectURL(fullBlob);
            if (status) status.innerText = "Ready";
            Notification.show("Mix preview ready", "success");
        } catch (err) {
            if (status) status.innerText = "Error";
            ErrorDisplay.show("Mixing Error", err.message);
            console.error(err);
        } finally {
            btn.disabled = false;
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

        let html = presets.map(p => `
            <div class="card voice-card" style="padding:16px; border-left:4px solid var(--accent);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="text-transform:uppercase;">${p}</strong>
                        <div style="font-size:0.7rem; opacity:0.5;">PRESET VOICE</div>
                    </div>
                    <button class="btn btn-secondary btn-sm" onclick="previewVoice('preset', '${p}')"><i class="fas fa-play"></i></button>
                </div>
            </div>
        `).join('');

        html += savedVoices.map(v => `
            <div class="card voice-card" style="padding:16px; border-left:4px solid var(--text-primary);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="text-transform:uppercase;">${v.name}</strong>
                        <div style="font-size:0.7rem; opacity:0.5;">${v.profile.type.toUpperCase()}</div>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-secondary btn-sm" onclick="previewVoice('${v.profile.type}', '${v.profile.value}')"><i class="fas fa-play"></i></button>
                        <button class="btn btn-danger btn-sm" onclick="deleteVoice('${v.name}')" style="padding:4px 8px;"><i class="fas fa-trash"></i></button>
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
            ...presets.map(p => `<option value="${p}">${p} (Preset)</option>`),
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
        speakerData.presets.forEach(p => profiles[p] = { type: 'preset', value: p });
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

    async previewVoice(type, value) {
        const player = document.getElementById('preview-player');
        try {
            const res = await fetch('/api/voice/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type, value, name: "Preview" })
            });
            const blob = await res.blob();
            player.src = URL.createObjectURL(blob);
            player.play();
        } catch (err) { console.error(err); }
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
    }
};
