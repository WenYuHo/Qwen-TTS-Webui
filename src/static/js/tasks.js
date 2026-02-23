import { TaskPoller } from './api.js';

export const TaskMonitor = {
    tasks: [],
    container: null,

    init(containerId) {
        this.container = document.getElementById(containerId);
        this.render();
    },

    addTask(taskId, type, metadata = {}) {
        const task = {
            id: taskId,
            type: type,
            status: 'pending',
            progress: 0,
            message: 'Initializing...',
            metadata: metadata,
            resultUrl: null,
            startTime: new Date()
        };
        this.tasks.unshift(task);
        this.render();

        TaskPoller.poll(taskId, (t) => {
            task.status = t.status;
            task.progress = t.progress;
            task.message = t.message;
            this.render();
        }).then(blob => {
            task.status = 'completed';
            task.progress = 100;
            task.message = 'Ready';
            task.resultUrl = URL.createObjectURL(blob);
            this.render();
        }).catch(err => {
            task.status = 'failed';
            task.message = err.message;
            this.render();
        });
    },

    render() {
        if (!this.container) return;

        if (this.tasks.length === 0) {
            this.container.innerHTML = '<p style="color:var(--text-secondary); font-size:0.8rem; text-align:center; padding:32px 16px; border:1px dashed var(--border); border-radius:12px; margin-top:8px;">No active tasks</p>';
            return;
        }

        this.container.innerHTML = this.tasks.map(t => `
            <div class="task-card" style="padding:14px; margin-bottom:12px; border-radius:12px; background:white; border:1px solid var(--border); box-shadow:var(--shadow-sm);">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
                    <div>
                        <div style="font-weight:700; font-size:0.8rem; color:var(--text-primary); text-transform:uppercase;">${t.type.replace('_', ' ')}</div>
                        <div style="font-size:0.7rem; color:var(--text-secondary);">${t.startTime.toLocaleTimeString()}</div>
                    </div>
                    <span class="badge" style="background:${this.getStatusBg(t.status)}; color:${this.getStatusColor(t.status)}; border:1px solid currentColor; font-size:0.65rem;">${t.status.toUpperCase()}</span>
                </div>

                <div style="font-size:0.75rem; color:var(--text-secondary); margin-bottom:10px; line-height:1.4;">${t.message}</div>

                <div class="progress-container" style="height:6px; background:var(--bg-sidebar); border-radius:3px; margin-bottom:12px; overflow:hidden;">
                    <div class="progress-bar" style="width:${t.progress}%; height:100%; background:var(--accent); transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);"></div>
                </div>

                ${t.status === 'completed' ? `
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-secondary btn-sm" style="flex:1; padding:6px; font-size:0.75rem;" onclick="window.playTaskResult('${t.id}')">
                            <i class="fas fa-play"></i> Play
                        </button>
                        <a class="btn btn-primary btn-sm" style="flex:1; padding:6px; font-size:0.75rem; text-decoration:none;" href="${t.resultUrl}" download="${t.type}_${t.id}.${this.getExtension(t.type)}">
                            <i class="fas fa-download"></i> Save
                        </a>
                    </div>
                ` : ''}

                ${t.status === 'failed' ? `
                    <button class="btn btn-secondary btn-sm" style="width:100%; padding:6px; font-size:0.75rem; color:var(--danger);" onclick="window.removeTask('${t.id}')">
                        <i class="fas fa-trash"></i> Dismiss
                    </button>
                ` : ''}
            </div>
        `).join('');
    },

    getStatusBg(status) {
        switch(status) {
            case 'completed': return 'rgba(16, 185, 129, 0.1)';
            case 'failed': return 'rgba(239, 68, 68, 0.1)';
            case 'processing': return 'rgba(99, 102, 241, 0.1)';
            default: return 'rgba(107, 114, 128, 0.1)';
        }
    },

    getStatusColor(status) {
        switch(status) {
            case 'completed': return 'var(--success)';
            case 'failed': return 'var(--danger)';
            case 'processing': return 'var(--accent)';
            default: return 'var(--text-secondary)';
        }
    },

    getExtension(type) {
        return type.includes('video') ? 'mp4' : 'wav';
    }
};

window.playTaskResult = (taskId) => {
    const task = TaskMonitor.tasks.find(t => t.id === taskId);
    if (task && task.resultUrl) {
        const player = document.getElementById('main-audio-player');
        if (task.type.includes('video')) {
             // For video, we might want to open in new tab or show in a modal
             // But for now, just let user download it
             window.open(task.resultUrl, '_blank');
        } else {
            player.src = task.resultUrl;
            player.play();
        }
    }
};

window.removeTask = (taskId) => {
    TaskMonitor.tasks = TaskMonitor.tasks.filter(t => t.id !== taskId);
    TaskMonitor.render();
};
