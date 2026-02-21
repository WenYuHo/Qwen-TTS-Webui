// studio.js - Voice Studio Logic
// Dependence: shared.js

const studio = {
    state: {
        designResult: null,
        cloneResult: null,
        lastUploadedPath: null
    },

    async handleUpload(file) {
        if (!file) return;
        document.getElementById('upload-name').innerText = "Uploading: " + file.name;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/voice/upload', {
                method: 'POST',
                body: formData
            });
            if (!res.ok) throw new Error("Upload failed");
            const data = await res.json();
            this.state.lastUploadedPath = data.filename;
            document.getElementById('upload-name').innerText = "✅ Uploaded: " + file.name;
            document.getElementById('btn-clone-test').disabled = false;
        } catch (e) {
            alert("Error: " + e.message);
            document.getElementById('upload-name').innerText = "❌ Upload failed";
        }
    },

    async testVoice(type) {
        const btn = document.getElementById(`btn-${type}-test`);
        const preview = document.getElementById(`${type}-preview`);
        const status = document.getElementById(`${type}-status`);

        btn.disabled = true;
        status.innerText = "Generating...";
        preview.style.display = 'flex';

        const text = document.getElementById(`${type}-test-text`).value;
        const value = type === 'design' ? document.getElementById('design-instruct').value : this.state.lastUploadedPath;

        const profile = { role: 'tester', type: type, value: value };

        try {
            const res = await fetch('/api/generate/segment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    profiles: [profile],
                    script: [{ role: 'tester', text }]
                })
            });

            if (!res.ok) throw new Error("Generation failed");

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            this.state[`${type}Result`] = { url, type, value };
            status.innerText = "Ready!";
        } catch (e) {
            alert("Error: " + e.message);
            status.innerText = "Error";
            preview.style.display = 'none';
        } finally {
            btn.disabled = false;
        }
    },

    playPreview(type) {
        const result = this.state[`${type}Result`];
        if (result && result.url) {
            const player = document.getElementById('studio-player');
            player.src = result.url;
            player.play();
        }
    },

    async saveVoice(type) {
        const result = this.state[`${type}Result`];
        if (!result) return;

        const name = prompt("Enter a name for this voice:");
        if (!name) return;

        // Generate a permanent preview sample for the library
        const profile = { role: name, type: result.type, value: result.value };
        await getVoicePreview(profile); // This caches it on the backend

        SpeakerStore.saveVoice({
            id: Date.now().toString(),
            name: name,
            type: result.type,
            value: result.value
        });

        this.renderLibrary();
        alert("Voice saved to library!");
    },

    renderLibrary() {
        const container = document.getElementById('studio-library');
        const voices = SpeakerStore.getVoices();

        container.innerHTML = '';
        if (voices.length === 0) {
            container.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--text-secondary); margin-top:20px;">Your library is empty.</p>';
            return;
        }

        voices.forEach(v => {
            const div = document.createElement('div');
            div.className = 'studio-card';
            div.style.padding = '16px';
            div.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div style="flex:1">
                        <strong style="display:block; font-size:1.1rem;">${v.name}</strong>
                        <span style="font-size:0.7rem; color:var(--text-secondary); text-transform:uppercase;">${v.type}</span>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-secondary btn-sm" onclick="studio.playLibraryPreview('${v.name}', '${v.type}', '${v.value}')">🔊</button>
                        <button class="btn btn-secondary btn-sm" onclick="studio.deleteVoice('${v.id}')" style="color:var(--danger)">×</button>
                    </div>
                </div>
            `;
            container.appendChild(div);
        });
    },

    async playLibraryPreview(role, type, value) {
        const blob = await getVoicePreview({ role, type, value });
        if (blob) {
            const player = document.getElementById('studio-player');
            player.src = URL.createObjectURL(blob);
            player.play();
        }
    },

    deleteVoice(id) {
        if (!confirm("Delete this voice?")) return;
        SpeakerStore.deleteVoice(id);
        this.renderLibrary();
    }
};

// Init
studio.renderLibrary();
window.studio = studio;
