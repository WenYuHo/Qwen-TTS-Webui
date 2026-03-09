// --- Task Management Module ---

export const TaskManager = {
    async refreshTasks() {
        const grids = document.querySelectorAll('.js-task-monitor-list');
        if (grids.length === 0) {
            console.warn("TaskManager: No grids found with class .js-task-monitor-list");
            return;
        }

        try {
            const resp = await fetch('/api/tasks');
            const tasks = await resp.json();
            console.log(`TaskManager: Fetched ${tasks.length} tasks`);

            const content = tasks.length === 0
                ? '<div class="card" style="border-style:dashed; opacity:0.6; text-align:center;">No active tasks</div>'
                : tasks.sort((a,b) => b.created_at - a.created_at).map(task => `
                <div class="card task-item" style="border-left: 4px solid ${this.getTaskColor(task.status)}; padding:12px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
                        <div>
                            <div class="task-item-meta">
                                <strong style="font-size:0.9rem;">${task.type.split('_').join(' ').toUpperCase()}</strong>
                                <span class="task-badge task-badge-${task.status}">${task.status}</span>
                            </div>
                            <div style="font-size:0.75rem; color:var(--text-secondary);">ID: ${task.id.split('-')[0]}... - ${new Date(task.created_at * 1000).toLocaleTimeString()}</div>
                        </div>
                        <button class="btn btn-danger btn-sm" onclick="cancelTask('${task.id}')" ${['completed', 'failed', 'cancelled'].includes(task.status) ? 'disabled' : ''} style="padding: 4px 8px; font-size: 0.7rem;" aria-label="Cancel task">
                            <i class="fas fa-times" aria-hidden="true"></i> Cancel
                        </button>
                    </div>

                    <div class="progress-bar-container" style="height:6px; margin-bottom:8px;" aria-label="Progress bar">
                        <div class="progress-bar-fill" style="width:${task.progress}%;" aria-valuenow="${task.progress}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>

                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div style="font-size:0.75rem; opacity:0.8; font-style:italic;">${task.message}</div>
                        <div style="font-size:0.75rem; font-weight:700;">${task.progress}%</div>
                    </div>
                </div>
            `).join('');

            grids.forEach(grid => { grid.innerHTML = content; });
        } catch (err) { console.error("Failed to load tasks", err); }
    },

    getTaskColor(status) {
        switch (status) {
            case 'pending': return 'var(--text-secondary)';
            case 'processing': return 'var(--accent)';
            case 'completed': return 'var(--success)';
            case 'failed': return 'var(--danger)';
            case 'cancelled': return '#f59e0b';
            default: return 'var(--border)';
        }
    },

    async cancelTask(id) {
        if (!confirm(`Cancel this task?`)) return;
        try {
            const resp = await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
            if (resp.ok) this.refreshTasks();
        } catch (err) { console.error("Cancel error", err); }
    },

    async clearCompletedTasks() {
        try {
            const resp = await fetch('/api/tasks');
            const tasks = await resp.json();
            const finished = tasks.filter(t => ['completed', 'failed', 'cancelled'].includes(t.status));

            for (const t of finished) {
                await fetch(`/api/tasks/${t.id}`, { method: 'DELETE' });
            }
            this.refreshTasks();
        } catch (err) { console.error("Clear error", err); }
    },

    pollTask(taskId, onComplete) {
        const statusText = document.getElementById('status-text') || document.getElementById('status-badge');

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/tasks/${taskId}`);
                const data = await res.json();

                if (data.status === 'completed') {
                    clearInterval(interval);
                    if (statusText) statusText.innerText = "Task Ready";
                    if (onComplete) onComplete(data);
                    else alert("Task Complete!");
                } else if (data.status === 'failed') {
                    clearInterval(interval);
                    if (statusText) statusText.innerText = "Task Failed";
                    alert(`Error: ${data.error}`);
                } else {
                    if (statusText) statusText.innerText = `Processing: ${data.progress}% - ${data.message}`;
                }
            } catch (err) {
                console.error("Polling error", err);
            }
        }, 2000);
    },

    async showHistoryModal() {
        const modal = document.getElementById('history-modal');
        const list = document.getElementById('history-list');
        if (!modal || !list) return;

        modal.style.display = 'flex';
        list.innerHTML = '<div class="volt-text" style="text-align:center; padding:20px;">FETCHING_HISTORY...</div>';

        try {
            const resp = await fetch('/api/tasks');
            const tasks = await resp.json();
            
            // Only show completed/failed/cancelled
            const history = tasks.filter(t => ['completed', 'failed', 'cancelled'].includes(t.status))
                                 .sort((a,b) => b.created_at - a.created_at);

            if (history.length === 0) {
                list.innerHTML = '<div style="text-align:center; opacity:0.5; padding:40px;">NO_HISTORY_FOUND</div>';
                return;
            }

            list.innerHTML = history.map(task => `
                <div class="card" style="border-left: 4px solid ${this.getTaskColor(task.status)}; background:rgba(255,255,255,0.02); padding:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <strong style="color:var(--accent); font-size:0.85rem;">${task.type.toUpperCase()}</strong>
                            <div style="font-size:0.65rem; opacity:0.6;">${new Date(task.created_at * 1000).toLocaleString()}</div>
                        </div>
                        <div style="display:flex; gap:8px;">
                            ${task.status === 'completed' ? `
                                <a href="/api/tasks/${task.id}/result" download="${task.type}_${task.id.substring(0,8)}.wav" class="btn btn-primary btn-sm" style="font-size:0.6rem;">
                                    <i class="fas fa-download"></i>
                                </a>
                                <button class="btn btn-secondary btn-sm" onclick="playTaskResult('${task.id}')" style="font-size:0.6rem;">
                                    <i class="fas fa-play"></i>
                                </button>
                            ` : ''}
                            <button class="btn btn-danger btn-sm" onclick="cancelTask('${task.id}')" title="Remove from history" style="font-size:0.6rem;">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div style="font-size:0.75rem; margin-top:8px; opacity:0.8;">${task.message}</div>
                </div>
            `).join('');
        } catch (err) {
            list.innerHTML = `<div class="volt-text" style="color:var(--danger)">ERROR_LOADING_HISTORY: ${err.message}</div>`;
        }
    },

    hideHistoryModal() {
        const modal = document.getElementById('history-modal');
        if (modal) modal.style.display = 'none';
    }
};
