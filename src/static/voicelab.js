// --- Voice Lab (Design, Clone, Mix) Module ---
import { TaskManager } from './task_manager.js';

export const VoiceLabManager = {
    async testVoiceDesign(btn) {
        const prompt = document.getElementById('design-prompt').value;
        if (!prompt) return alert("Please enter a style prompt.");

        const container = document.getElementById('design-preview-container');
        const status = document.getElementById('design-status');
        const player = document.getElementById('preview-player');

        container.style.display = 'block';
        status.innerText = "Designing...";
        btn.disabled = true;

        try {
            const profile = { type: 'design', value: prompt };
            const res = await fetch('/api/generate/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: "This is a preview of your designed voice.", profile: profile })
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
        } catch (err) {
            status.innerText = "Error";
            console.error(err);
        } finally {
            btn.disabled = false;
        }
    },

    async testVoiceClone(btn) {
        const fileInput = document.getElementById('clone-file');
        if (!window.state.voicelab.lastClonedPath && !fileInput.files.length) {
            return alert("Please upload or record reference audio first.");
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
        } catch (err) {
            status.innerText = "Error";
            console.error(err);
        } finally {
            btn.disabled = false;
        }
    },

    async testVoiceMix(btn) {
        const vA = document.getElementById('mix-voice-a').value;
        const vB = document.getElementById('mix-voice-b').value;
        const wA = parseInt(document.getElementById('mix-weight-a').value) / 100;
        const wB = parseInt(document.getElementById('mix-weight-b').value) / 100;

        if (!vA || !vB) return alert("Select two voices to mix.");

        const container = document.getElementById('mix-preview-container');
        const status = document.getElementById('mix-status');
        const player = document.getElementById('preview-player');

        container.style.display = 'block';
        status.innerText = "Mixing...";
        btn.disabled = true;

        try {
            const profiles = window.getAllProfiles();
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
            status.innerText = "Ready";
        } catch (err) {
            status.innerText = "Error";
            console.error(err);
        } finally {
            btn.disabled = false;
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
    }
};
