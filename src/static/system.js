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
        } catch (err) {
            console.error("Failed to fetch inventory:", err);
        }
    },

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
