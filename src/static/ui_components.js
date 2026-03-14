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

        // Apply current subtitle settings from UI
        const subEnabled = document.getElementById('video-subtitles')?.checked ?? true;
        const subPos = document.getElementById('video-sub-pos')?.value ?? 'bottom';
        const subSize = document.getElementById('video-sub-size')?.value ?? '24';

        overlay.style.display = subEnabled ? 'block' : 'none';
        overlay.style.fontSize = `${subSize}px`;
        
        if (subPos === 'top') {
            overlay.style.bottom = 'auto';
            overlay.style.top = '10%';
            overlay.style.transform = 'none';
        } else if (subPos === 'middle' || subPos === 'center') {
            overlay.style.bottom = 'auto';
            overlay.style.top = '50%';
            overlay.style.transform = 'translateY(-50%)';
        } else {
            overlay.style.bottom = '15%';
            overlay.style.top = 'auto';
            overlay.style.transform = 'none';
        }

        // Load subtitles if available
        if (srtFilename) {
            try {
                const res = await fetch(`/api/video/download/${srtFilename}`);
                const srtText = await res.text();
                this.setupSubtitles(player, overlay, srtText);
            } catch (err) { console.error("Failed to load subtitles", err); }
        }

        modal.style.display = 'flex';
        if (title) title.focus();
        player.play();

        this._handleEsc = (e) => {
            if (e.key === 'Escape') this.hide();
        };
        document.addEventListener('keydown', this._handleEsc);
    },

    hide() {
        const modal = document.getElementById('video-modal');
        const player = document.getElementById('video-modal-player');
        if (modal) modal.style.display = 'none';
        if (player) {
            player.pause();
            player.src = '';
        }
        if (this._handleEsc) {
            document.removeEventListener('keydown', this._handleEsc);
            this._handleEsc = null;
        }
    },

    setupSubtitles(video, container, srtText) {
        const parseSRT = (data) => {
            const items = [];
            const blocks = data.split('\n\n');
            blocks.forEach(block => {
                const lines = block.split('\n');
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
                <button class="btn btn-danger btn-sm" style="padding:2px 6px;" onclick="this.parentElement.parentElement.remove()" aria-label="Close error message" title="Close error message"><i class="fas fa-times" aria-hidden="true"></i></button>
            </div>
            <div style="font-size:0.75rem; color:#ffb3c1; margin-bottom:12px; line-height:1.4;">
                ${detail}
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; background:#000; padding:8px; border:1px solid #330008;">
                <div id="error-trace-text" style="font-size:0.6rem; font-family:var(--font-mono); color:var(--danger); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:280px;">
                    TRACE: ${new Date().toISOString()} | ${detail}
                </div>
                <button class="btn btn-secondary btn-sm" style="padding:2px 8px; font-size:0.6rem;" onclick="copyErrorTrace(this)">COPY</button>
            </div>
        `;

        container.prepend(errorModal);
    }
};

window.copyErrorTrace = (btn) => {
    const trace = document.getElementById('error-trace-text').innerText;
    navigator.clipboard.writeText(trace).then(() => {
        const original = btn.innerText;
        btn.innerText = "COPIED!";
        btn.style.color = "var(--success)";
        setTimeout(() => {
            btn.innerText = original;
            btn.style.color = "";
        }, 2000);
    });
};

export const HelpManager = {
    helpContent: {
        speech: `### 🎙️ Voice Studio (v2.1)
1. **Design:** Use natural language (e.g. "A deep radio host voice") to create new AI voices.
2. **Clone:** Upload a 3-10s clip to clone any speaker using zero-shot ICL.
3. **Mix:** Slide between two voices to create a perfect hybrid.
*Tip: Use the 'Preview Text' bar to test your creations before saving.*`,
        
        projects: `### 🎭 Project Studio
1. **Draft:** Write your script using 'Speaker: Text' lines. Use the **SAMPLES** menu for quick demos!
2. **Promote:** Click 'Promote' to turn your text into granular, editable blocks.
3. **Produce:** Mix in BGM, apply EQ/Reverb, and hit 'Produce Final'.
*Video: Toggle 'Enable Video' to generate AI visuals for your story.*`,
        
        dubbing: `### 🌍 Dubbing & S2S
1. **Dubbing:** Upload a video, click 'Diarize' to find speakers, assign voices, and translate.
2. **S2S:** Speak into your mic or upload a file to change the voice while keeping your emotion.
*Tip: Use 'Low-Latency Streaming' for instant feedback.*`,
        
        assets: "### 📦 Asset Library\n- Upload and manage background music (BGM) and sound effects (SFX).\n- Use supported formats: MP3, WAV.\n- Metadata like duration and sample rate are auto-extracted.",
        
        system: "### ⚙️ System Manager\n- **Inventory:** Download and verify model checkpoints.\n- **Performance:** Benchmark engine speed.\n- **Theme:** Customize the Studio accent color (Volt)."
    },

    show(view) {
        const content = this.helpContent[view] || "Select a view to see help.";
        
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.style.display = 'flex';

        const closeHelp = () => {
            document.removeEventListener('keydown', handleEsc);
            overlay.remove();
        };

        const handleEsc = (e) => {
            if (e.key === 'Escape') closeHelp();
        };

        overlay.onclick = (e) => { if(e.target === overlay) closeHelp(); };
        document.addEventListener('keydown', handleEsc);

        const modal = document.createElement('div');
        modal.className = 'card-brutalist modal-content';
        modal.style.maxWidth = '500px';
        modal.style.padding = '32px';

        modal.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border-bottom:2px solid var(--accent); padding-bottom:12px;">
                <h2 style="margin:0; font-size:1.2rem;" tabindex="-1">QUICK START GUIDE</h2>
                <button class="btn btn-danger btn-sm" aria-label="Close help modal" title="Close help modal"><i class="fas fa-times"></i></button>
            </div>
            <div style="font-size:0.9rem; line-height:1.6; font-family:var(--font-mono); color:var(--text-secondary);">
                ${content.replace(/\n/g, '<br>').replace(/### (.+)/g, '<strong style="color:var(--accent)">$1</strong>')}
            </div>
            <button class="btn btn-primary btn-sm" style="width:100%; margin-top:24px;">ACKNOWLEDGE</button>
        `;

        modal.querySelectorAll('button').forEach(btn => btn.onclick = closeHelp);

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        const heading = modal.querySelector('h2');
        if (heading) heading.focus();
    }
};
