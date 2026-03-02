// --- UI Components Module (Modals, Notifications) ---

export const VideoModal = {
    async show(videoFilename, srtFilename) {
        const modal = document.getElementById('video-modal');
        const player = document.getElementById('video-modal-player');
        const overlay = document.getElementById('video-subtitle-overlay');
        const download = document.getElementById('video-modal-download');
        const title = document.getElementById('video-modal-title');

        if (!modal || !player) return;

        title.innerText = `Preview: ${videoFilename}`;
        player.src = `/api/video/download/${videoFilename}`;
        download.href = `/api/video/download/${videoFilename}`;
        overlay.innerText = '';

        // Load subtitles if available
        if (srtFilename) {
            try {
                const res = await fetch(`/api/video/download/${srtFilename}`);
                const srtText = await res.text();
                this.setupSubtitles(player, overlay, srtText);
            } catch (err) { console.error("Failed to load subtitles", err); }
        }

        modal.style.display = 'flex';
        player.play();
    },

    hide() {
        const modal = document.getElementById('video-modal');
        const player = document.getElementById('video-modal-player');
        if (modal) modal.style.display = 'none';
        if (player) {
            player.pause();
            player.src = '';
        }
    },

    setupSubtitles(video, container, srtText) {
        const parseSRT = (data) => {
            const items = [];
            const blocks = data.split('

');
            blocks.forEach(block => {
                const lines = block.split('
');
                if (lines.length >= 3) {
                    const times = lines[1].split(' --> ');
                    items.push({
                        start: this.timestampToSeconds(times[0]),
                        end: this.timestampToSeconds(times[1]),
                        text: lines.slice(2).join(' ')
                    });
                }
            });
            return items;
        };

        const subs = parseSRT(srtText);
        
        video.ontimeupdate = () => {
            const time = video.currentTime;
            const active = subs.find(s => time >= s.start && time <= s.end);
            container.innerText = active ? active.text : '';
        };
    },

    timestampToSeconds(ts) {
        const [hms, ms] = ts.split(',');
        const [h, m, s] = hms.split(':').map(parseFloat);
        return h * 3600 + m * 60 + s + (parseFloat(ms) / 1000);
    }
};

export const Notification = {
    show(message, type = 'info') {
        // Simple alert for now, can be upgraded to a toast later
        console.log(`[${type.toUpperCase()}] ${message}`);
        // toast implementation here...
    }
};
