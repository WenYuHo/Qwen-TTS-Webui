// --- System Metrics Footer Module ---

export const MetricsManager = {
    intervalId: null,

    start() {
        if (this.intervalId) return;
        this.refresh();
        this.intervalId = setInterval(() => this.refresh(), 3000);
    },

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    },

    async refresh() {
        try {
            // 1. Fetch Stats
            const statsRes = await fetch('/api/system/stats');
            if (!statsRes.ok) return;
            const stats = await statsRes.json();
            
            this.updateMetric('footer-cpu', stats.cpu_percent + '%');
            this.updateMetric('footer-ram', stats.ram_percent + '%');
            
            const gpuContainer = document.getElementById('footer-gpu-container');
            if (stats.gpu && gpuContainer) {
                gpuContainer.style.display = 'block';
                this.updateMetric('footer-vram', stats.gpu.vram_percent.toFixed(0) + '%');
            } else if (gpuContainer) {
                gpuContainer.style.display = 'none';
            }

            // 2. Fetch Tasks count
            const tasksRes = await fetch('/api/tasks');
            if (tasksRes.ok) {
                const tasks = await tasksRes.json();
                const activeCount = tasks.filter(t => t.status !== 'completed' && t.status !== 'failed').length;
                this.updateMetric('footer-tasks', activeCount);
            }

        } catch (e) {
            // Silently fail for background metrics
        }
    },

    updateMetric(id, value) {
        const el = document.getElementById(id);
        if (el) {
            // Subtle color change if high usage
            if (typeof value === 'string' && value.includes('%')) {
                const num = parseInt(value);
                if (num > 90) el.style.color = 'var(--danger)';
                else if (num > 70) el.style.color = 'var(--warn)';
                else el.style.color = 'var(--accent)';
            }
            el.innerText = value;
        }
    }
};
