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
            
            // Also load phonemes when inventory is fetched (on view switch)
            this.loadPhonemes();
        } catch (err) {
            console.error("Failed to fetch inventory:", err);
        }
    },

    async loadPhonemes() {
        const list = document.getElementById('phoneme-list');
        if (!list) return;

        try {
            const res = await fetch('/api/system/phonemes');
            const data = await res.json();
            this.renderPhonemeList(data.overrides);
        } catch (err) {
            console.error("Failed to load phonemes:", err);
        }
    },

    renderPhonemeList(overrides) {
        const list = document.getElementById('phoneme-list');
        if (!list) return;

        list.innerHTML = '';
        Object.entries(overrides).forEach(([word, phonetic]) => {
            const item = document.createElement('div');
            item.className = 'card';
            item.style.padding = '8px 12px';
            item.style.display = 'flex';
            item.style.justifyContent = 'space-between';
            item.style.alignItems = 'center';
            item.style.fontSize = '0.85rem';
            item.style.background = 'rgba(255,255,255,0.02)';

            item.innerHTML = `
                <div>
                    <strong>${word}</strong> 
                    <i class="fas fa-arrow-right" style="margin:0 8px; opacity:0.5; font-size:0.7rem;"></i> 
                    <span style="color:var(--accent)">${phonetic}</span>
                </div>
                <button class="btn btn-danger btn-sm" onclick="removePhonemeOverride('${word}')" style="padding:2px 6px;">
                    <i class="fas fa-times"></i>
                </button>
            `;
            list.appendChild(item);
        });
    },

    async addPhonemeOverride() {
        const wordInput = document.getElementById('phoneme-word');
        const phoneticInput = document.getElementById('phoneme-replacement');
        const word = wordInput.value.trim();
        const phonetic = phoneticInput.value.trim();

        if (!word || !phonetic) return;

        try {
            const res = await fetch('/api/system/phonemes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ word, phonetic })
            });
            const data = await res.json();
            this.renderPhonemeList(data.overrides);
            wordInput.value = '';
            phoneticInput.value = '';
        } catch (err) {
            console.error("Failed to add phoneme:", err);
        }
    },

    async removePhonemeOverride(word) {
        try {
            const res = await fetch(`/api/system/phonemes/${word}`, { method: 'DELETE' });
            const data = await res.json();
            this.renderPhonemeList(data.overrides);
        } catch (err) {
            console.error("Failed to remove phoneme:", err);
        }
    },

    async importPhonemes(input) {
        if (!input.files || input.files.length === 0) return;
        const file = input.files[0];
        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const data = JSON.parse(e.target.result);
                const res = await fetch('/api/system/phonemes/bulk', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await res.json();
                this.renderPhonemeList(result.overrides);
                alert("Phonemes imported successfully");
            } catch (err) {
                console.error("Bulk import failed:", err);
                alert("Failed to import phonemes. Ensure file is valid JSON.");
            }
        };
        reader.readAsText(file);
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
            console.log("Watermark settings updated");
        } catch (err) {
            console.error("Failed to update settings:", err);
        }
    },

    async loadSystemSettings() {
        try {
            const res = await fetch('/api/system/settings');
            const data = await res.json();

            if (document.getElementById('watermark-audio')) {
                document.getElementById('watermark-audio').checked = data.watermark_audio;
            }
            if (document.getElementById('watermark-video')) {
                document.getElementById('watermark-video').checked = data.watermark_video;
            }
        } catch (err) {
            console.error("Failed to load settings:", err);
        }
    }
    };

    async triggerDownload(repoId) {
        try {
            const res = await fetch('/api/models/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_id: repoId })
            });
            const data = await res.json();
            alert(`Download started for ${repoId}. Check the Task Monitor for progress.`);
            if (window.refreshTasks) window.refreshTasks();
        } catch (err) {
            console.error("Download trigger failed:", err);
            alert("Failed to start download. Check console.");
        }
    }
};
