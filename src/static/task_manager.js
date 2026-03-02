// --- Task Management Module ---

export const TaskManager = {
    async refreshTasks() {
        const grids = document.querySelectorAll('.js-task-monitor-list');
        if (grids.length === 0) return;

        try {
            const resp = await fetch('/api/tasks/');
            const tasks = await resp.json();

            const content = tasks.length === 0
                ? '<div class="card" style="border-style:dashed; opacity:0.6; text-align:center;">No active tasks</div>'
                : tasks.sort((a,b) => b.created_at - a.created_at).map(task => `
                <div class="card task-item" style="border-left: 4px solid ${this.getTaskColor(task.status)};">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
                        <div>
                            <div class="task-item-meta">
                                <strong style="font-size:0.9rem;">${task.type.split('_').join(' ').toUpperCase()}</strong>
                                <span class="task-badge task-badge-${task.status}">${task.status}</span>
                            </div>
                            <div style="font-size:0.75rem; color:var(--text-secondary);">ID: ${task.id.split('-')[0]}... • ${new Date(task.created_at * 1000).toLocaleTimeString()}</div>
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
            const resp = await fetch('/api/tasks/');
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
    }
};
