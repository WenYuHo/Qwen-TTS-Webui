import sys

with open('src/static/app.js', 'r') as f:
    content = f.read()

old_render = """grid.innerHTML = tasks.sort((a,b) => b.created_at - a.created_at).map(task => `
            <div class="card task-item" style="display:flex; justify-content:space-between; align-items:center; border-left: 4px solid ${getTaskColor(task.status)};">
                <div style="flex:1;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <strong style="font-size:0.9rem;">${task.type.toUpperCase()}</strong>
                        <span style="font-size:0.8rem; opacity:0.7;">${task.status}</span>
                    </div>
                    <div class="progress-bar-container" style="height:4px; margin-bottom:4px;">
                        <div class="progress-bar-fill" style="width:${task.progress}%;"></div>
                    </div>
                    <div style="font-size:0.75rem; opacity:0.8;">${task.message}</div>
                </div>
                <div style="margin-left:16px;">
                    <button class="btn btn-danger btn-sm" onclick="cancelTask('${task.id}')" ${['completed', 'failed', 'cancelled'].includes(task.status) ? 'disabled' : ''}>
                        <i class="fas fa-times"></i> Cancel
                    </button>
                </div>
            </div>
        `).join('');"""

new_render = """grid.innerHTML = tasks.sort((a,b) => b.created_at - a.created_at).map(task => `
            <div class="card task-item" style="border-left: 4px solid ${getTaskColor(task.status)};">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
                    <div>
                        <div class="task-item-meta">
                            <strong style="font-size:0.9rem;">${task.type.split('_').join(' ').toUpperCase()}</strong>
                            <span class="task-badge task-badge-${task.status}">${task.status}</span>
                        </div>
                        <div style="font-size:0.75rem; color:var(--text-secondary);">ID: ${task.id.split('-')[0]}... • ${new Date(task.created_at * 1000).toLocaleTimeString()}</div>
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="cancelTask('${task.id}')" ${['completed', 'failed', 'cancelled'].includes(task.status) ? 'disabled' : ''} style="padding: 4px 8px; font-size: 0.7rem;">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                </div>

                <div class="progress-bar-container" style="height:6px; margin-bottom:8px;">
                    <div class="progress-bar-fill" style="width:${task.progress}%;"></div>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size:0.75rem; opacity:0.8; font-style:italic;">${task.message}</div>
                    <div style="font-size:0.75rem; font-weight:700;">${task.progress}%</div>
                </div>
            </div>
        `).join('');"""

content = content.replace(old_render, new_render)

with open('src/static/app.js', 'w') as f:
    f.write(content)
