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
        const container = document.getElementById('toast-container');
        if (!container) {
            console.log(`[${type.toUpperCase()}] ${message}`);
            return;
        }

        const toast = document.createElement('div');
        toast.className = `card-brutalist toast toast-${type}`;
        toast.style.padding = '12px 20px';
        toast.style.minWidth = '250px';
        toast.style.pointerEvents = 'auto';
        toast.style.animation = 'viewEnter 0.3s ease-out';
        toast.style.display = 'flex';
        toast.style.alignItems = 'center';
        toast.style.gap = '12px';
        toast.style.boxShadow = '4px 4px 0px #000';

        const icons = {
            info: 'fa-info-circle',
            success: 'fa-check-circle',
            warn: 'fa-exclamation-triangle',
            error: 'fa-times-circle'
        };

        toast.innerHTML = `
            <i class="fas ${icons[type] || 'fa-bell'}" style="font-size:1.1rem;"></i>
            <div style="flex:1; font-size:0.85rem; font-weight:700; font-family:var(--font-mono);">${message.toUpperCase()}</div>
        `;

        container.appendChild(toast);

        // Auto-dismiss
        setTimeout(() => {
            toast.style.animation = 'viewExit 0.3s ease-in forwards';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
};

export const ErrorDisplay = {
    show(title, detail) {
        // We reuse the video modal structure or create a generic one
        // For speed, let's use a specialized toast-like error modal
        const container = document.getElementById('toast-container');
        if (!container) return;

        const errorModal = document.createElement('div');
        errorModal.className = 'card-brutalist';
        errorModal.style.borderColor = 'var(--danger)';
        errorModal.style.background = '#1a0005';
        errorModal.style.width = '400px';
        errorModal.style.pointerEvents = 'auto';
        errorModal.style.animation = 'viewEnter 0.4s cubic-bezier(0.2, 0.8, 0.2, 1)';
        errorModal.style.zIndex = '10001';

        errorModal.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid var(--danger); padding-bottom:8px;">
                <strong style="color:var(--danger); font-family:var(--font-mono); font-size:0.9rem;">
                    <i class="fas fa-exclamation-triangle"></i> ${title.toUpperCase()}
                </strong>
                <button class="btn btn-danger btn-sm" style="padding:2px 6px;" onclick="this.parentElement.parentElement.remove()"><i class="fas fa-times"></i></button>
            </div>
            <div style="font-size:0.75rem; color:#ffb3c1; margin-bottom:12px; line-height:1.4;">
                ${detail}
            </div>
            <div style="font-size:0.6rem; background:#000; padding:8px; font-family:var(--font-mono); color:var(--danger); border:1px solid #330008; max-height:100px; overflow:auto;">
                TRACE: ${new Date().toISOString()} | API_ERR_500
            </div>
        `;

        container.prepend(errorModal);
    }
};

export const HelpManager = {
    helpContent: {
        speech: "### Voice Studio\n- **Design:** Describe a voice to generate a unique profile.\n- **Clone:** Upload audio to replicate a specific person.\n- **Mix:** Combine two existing voices with custom weights.",
        projects: "### Project Studio\n- **Draft:** Write your script using 'Role: Text' format.\n- **Production:** Manage granular blocks and background music.\n- **Video:** Enable LTX-Video for AI-narrated segments.",
        dubbing: "### Dubbing & S2S\n- **Dubbing:** Translate and re-voice videos/audio automatically.\n- **S2S:** Perform real-time expressive voice conversion.",
        assets: "### Asset Library\n- Upload and manage background music (BGM) and sound effects (SFX).\n- Use supported formats: MP3, WAV.",
        system: "### System Manager\n- **Inventory:** Download and verify model checkpoints.\n- **Performance:** Benchmark engine speed and identify bottlenecks.\n- **Audit:** Track all AI generation activity."
    },

    show(view) {
        const content = this.helpContent[view] || "Select a view to see help.";
        
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.style.display = 'flex';
        overlay.onclick = (e) => { if(e.target === overlay) overlay.remove(); };

        const modal = document.createElement('div');
        modal.className = 'card-brutalist';
        modal.style.maxWidth = '500px';
        modal.style.padding = '32px';
        modal.style.animation = 'viewEnter 0.2s ease-out';

        modal.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border-bottom:2px solid var(--accent); padding-bottom:12px;">
                <h2 style="margin:0; font-size:1.2rem;">COMMAND REFERENCE</h2>
                <button class="btn btn-danger btn-sm" onclick="this.parentElement.parentElement.parentElement.remove()"><i class="fas fa-times"></i></button>
            </div>
            <div style="font-size:0.9rem; line-height:1.6; font-family:var(--font-mono); color:var(--text-secondary);">
                ${content.replace(/\n/g, '<br>').replace(/### (.+)/g, '<strong style="color:var(--accent)">$1</strong>')}
            </div>
            <button class="btn btn-secondary btn-sm" style="width:100%; margin-top:24px;" onclick="this.parentElement.parentElement.remove()">ACKNOWLEDGE</button>
        `;

        overlay.appendChild(modal);
        document.body.appendChild(overlay);
    }
};
