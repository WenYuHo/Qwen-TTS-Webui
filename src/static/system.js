// --- System & Model Management Module ---

export const SystemManager = {
    async fetchInventory() {
        const list = document.getElementById('model-inventory-list');
        if (!list) return;

        try {
            const res = await fetch('/api/models/inventory');
            const data = await res.json();
            
            list.innerHTML = '';
            data.models.forEach(model => {
                const card = document.createElement('div');
                card.className = 'card';
                card.style.padding = '12px';
                card.style.background = 'rgba(255,255,255,0.05)';
                card.style.display = 'flex';
                card.style.alignItems = 'center';
                card.style.justifyContent = 'space-between';
                card.style.gap = '12px';
                
                const icon = model.type === 'video' ? 'fa-video' : 'fa-music';
                const statusClass = model.status === 'downloaded' ? 'badge-success' : 'badge-warn';
                const statusLabel = model.status === 'downloaded' ? 'Ready' : 'Missing';
                
                card.innerHTML = `
                    <div style="display:flex; align-items:center; gap:12px;">
                        <i class="fas ${icon}" style="color:var(--accent); font-size:1.2rem;"></i>
                        <div style="display:flex; flex-direction:column;">
                            <span style="font-weight:bold; font-size:0.9rem;">${model.key}</span>
                            <span style="font-size:0.75rem; opacity:0.6;">${model.repo_id}</span>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:12px;">
                        <span class="badge ${statusClass}">${statusLabel}</span>
                        ${model.status === 'missing' ? `<button class="btn btn-primary btn-sm" onclick="triggerDownload('${model.repo_id}')"><i class="fas fa-download"></i></button>` : ''}
                    </div>
                `;
                list.appendChild(card);
            });
            
            this.loadPhonemes();
        } catch (err) { console.error("Failed to fetch inventory:", err); }
    },

    async triggerDownload(repoId) {
        try {
            const res = await fetch('/api/models/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_id: repoId })
            });
            if (window.refreshTasks) window.refreshTasks();
            alert(`Download started for ${repoId}.`);
        } catch (err) { alert("Download failed"); }
    },

    async loadPhonemes() {
        const list = document.getElementById('phoneme-list');
        if (!list) return;
        try {
            const res = await fetch('/api/system/phonemes');
            const data = await res.json();
            this.renderPhonemeList(data.overrides);
        } catch (err) { console.error("Failed to load phonemes:", err); }
    },

    renderPhonemeList(overrides) {
        const list = document.getElementById('phoneme-list');
        if (!list) return;
        list.innerHTML = Object.entries(overrides).map(([word, phonetic]) => `
            <div class="card" style="padding:8px 12px; display:flex; justify-content:space-between; align-items:center; font-size:0.85rem; background:rgba(255,255,255,0.02);">
                <div><strong>${word}</strong> <i class="fas fa-arrow-right" style="margin:0 8px; opacity:0.5;"></i> <span style="color:var(--accent)">${phonetic}</span></div>
                <button class="btn btn-danger btn-sm" onclick="removePhonemeOverride('${word}')" style="padding:2px 6px;"><i class="fas fa-times"></i></button>
            </div>
        `).join('');
    },

    async addPhonemeOverride() {
        const wI = document.getElementById('phoneme-word');
        const pI = document.getElementById('phoneme-replacement');
        if (!wI.value || !pI.value) return;
        try {
            const res = await fetch('/api/system/phonemes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ word: wI.value, phonetic: pI.value })
            });
            const data = await res.json();
            this.renderPhonemeList(data.overrides);
            wI.value = ''; pI.value = '';
        } catch (err) { console.error(err); }
    },

    async removePhonemeOverride(word) {
        try {
            const res = await fetch(`/api/system/phonemes/${word}`, { method: 'DELETE' });
            const data = await res.json();
            this.renderPhonemeList(data.overrides);
        } catch (err) { console.error(err); }
    },

    async importPhonemes(input) {
        if (!input.files?.length) return;
        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const res = await fetch('/api/system/phonemes/bulk', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: e.target.result
                });
                const result = await res.json();
                this.renderPhonemeList(result.overrides);
            } catch (err) { alert("Import failed"); }
        };
        reader.readAsText(input.files[0]);
    },

    async updateWatermarkSettings() {
        const audio = document.getElementById('watermark-audio').checked;
        const video = document.getElementById('watermark-video').checked;
        try {
            await fetch('/api/system/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ watermark_audio: audio, watermark_video: video })
            });
        } catch (err) { console.error(err); }
    },

    async loadSystemSettings() {
        try {
            const res = await fetch('/api/system/settings');
            const data = await res.json();
            if (document.getElementById('watermark-audio')) document.getElementById('watermark-audio').checked = data.watermark_audio;
            if (document.getElementById('watermark-video')) document.getElementById('watermark-video').checked = data.watermark_video;
        } catch (err) { console.error(err); }
    },

    async fetchAuditLog() {
        const list = document.getElementById('audit-log-list');
        if (!list) return;
        try {
            const res = await fetch('/api/system/audit');
            const data = await res.json();
            this.renderAuditLog(data.log);
        } catch (err) { console.error(err); }
    },

    renderAuditLog(log) {
        const list = document.getElementById('audit-log-list');
        if (!list) return;
        if (!log.length) { list.innerHTML = '<div style="text-align:center; opacity:0.5; padding:20px;">No events recorded</div>'; return; }
        list.innerHTML = log.sort((a,b) => b.timestamp - a.timestamp).map(e => `
            <div class="card" style="padding:8px 12px; font-size:0.75rem; background:rgba(255,255,255,0.01); border-color:rgba(255,255,255,0.05); margin-bottom:4px;">
                <div style="display:flex; justify-content:space-between;">
                    <strong style="color:var(--accent)">${e.type.toUpperCase()}</strong>
                    <span style="opacity:0.5;">${new Date(e.timestamp * 1000).toLocaleTimeString()}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:4px;">
                    <span>${e.status}</span>
                    <span style="opacity:0.4; font-family:monospace;">${JSON.stringify(e.metadata).substring(0, 40)}...</span>
                </div>
            </div>
        `).join('');
    }
};
