import { TaskPoller } from './api.js';

export async function renderSystemView() {
    const invList = document.getElementById('model-inventory-list');
    const stats = document.getElementById('system-stats');
    if (!invList || !stats) return;

    try {
        const res = await fetch('/api/models/inventory');
        const data = await res.json();
        invList.innerHTML = '';
        data.models.forEach(m => {
            const div = document.createElement('div');
            div.style.padding = '12px';
            div.style.background = 'var(--bg-sidebar)';
            div.style.border = '1px solid var(--border)';
            div.style.borderRadius = '10px';
            div.style.display = 'flex';
            div.style.justifyContent = 'space-between';
            div.style.alignItems = 'center';

            div.innerHTML = `
                <div>
                    <div style="font-weight:600; font-size:0.9rem;">${m.key}</div>
                    <div style="font-size:0.75rem; color:var(--text-secondary);">${m.repo_id}</div>
                </div>
                <div>
                    ${m.status === 'downloaded'
                        ? '<span class="badge" style="background:var(--success); color:white;">Ready</span>'
                        : `<button class="btn btn-primary btn-sm" onclick="downloadModel('${m.repo_id}')"><i class="fas fa-download"></i> Download</button>`}
                </div>
            `;
            invList.appendChild(div);
        });
    } catch (e) { invList.innerText = "Failed to load inventory"; }

    try {
        const res = await fetch('/api/health');
        const data = await res.json();
        stats.innerHTML = `
            <div style="margin-bottom:8px;"><strong>Status:</strong> ${data.status}</div>
            <div style="margin-bottom:8px;"><strong>Device:</strong> ${data.device.type} (CUDA: ${data.device.cuda_available})</div>
            <div style="margin-bottom:8px;"><strong>CPU:</strong> ${data.performance.cpu_percent}%</div>
            <div style="margin-bottom:8px;"><strong>Memory:</strong> ${data.performance.memory_percent}%</div>
        `;
    } catch (e) { stats.innerText = "Failed to load stats"; }
}

export async function downloadModel(repoId) {
    const statusText = document.getElementById('status-text');
    statusText.innerText = `Starting download for ${repoId}...`;
    try {
        const res = await fetch('/api/models/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ repo_id: repoId })
        });
        const { task_id } = await res.json();
        await TaskPoller.poll(task_id, (task) => {
            statusText.innerText = `Downloading ${repoId}: ${task.progress}%`;
        });
        statusText.innerText = "Download complete!";
        renderSystemView();
    } catch (e) {
        alert("Download failed: " + e.message);
        statusText.innerText = "Download failed";
    }
}
