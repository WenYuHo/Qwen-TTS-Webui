// --- Production & Studio Module ---
import { Notification, ErrorDisplay } from './ui_components.js';

export const ProductionManager = {
    async generatePodcast() {
        const statusText = document.getElementById('status-badge');
        const bgm_mood = document.getElementById('bgm-select').value;
        const ducking_level = parseFloat(document.getElementById('ducking-range').value) / 100.0;
        const streamEnabled = document.getElementById('stream-podcast').checked;
        const masterAcx = document.getElementById('master-acx').checked;
        const globalTemperature = parseFloat(document.getElementById('global-temperature').value) || 0.9;
        
        // Audio Effects
        const eqPreset = document.getElementById('audio-eq').value;
        const reverbLevel = parseFloat(document.getElementById('audio-reverb').value) / 100.0;

        // Video Options
        const videoEnabled = document.getElementById('video-enabled').checked;
        const videoPrompt = document.getElementById('video-prompt').value;
        const [width, height] = document.getElementById('video-res').value.split('x').map(Number);
        const numFrames = parseInt(document.getElementById('video-frames').value);
        const guidanceScale = parseFloat(document.getElementById('video-guidance').value);
        const inferenceSteps = parseInt(document.getElementById('video-steps').value);
        const seed = parseInt(document.getElementById('video-seed').value);
        const maxShift = parseFloat(document.getElementById('video-max-shift').value) || null;
        const baseShift = parseFloat(document.getElementById('video-base-shift').value) || null;
        const terminal = parseFloat(document.getElementById('video-terminal').value) || null;

        const productionView = document.getElementById('canvas-production-view');
        const isProduction = productionView && productionView.style.display === 'flex';

        let script = [];
        if (isProduction) {
            script = window.CanvasManager.blocks.map(b => ({
                role: b.role,
                text: b.text,
                language: b.language || 'auto',
                pause_after: b.pause_after || 0.5,
                temperature: b.temperature || null
            }));
        } else {
            script = window.parseScript(document.getElementById('script-editor').value);
        }

        if (script.length === 0) return Notification.show("Script is empty", "warn");
        const profiles = await window.getAllProfiles();

        try {
            if (statusText) statusText.innerText = videoEnabled ? "Generating Narrated Video..." : "Producing Podcast...";
            
            if (videoEnabled) {
                const firstBlock = script[0];
                const voiceProfile = profiles[firstBlock.role];
                
                const res = await fetch('/api/video/narrated', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        prompt: videoPrompt || firstBlock.text,
                        narration_text: firstBlock.text,
                        voice_profile: voiceProfile,
                        width: width,
                        height: height,
                        num_frames: numFrames,
                        guidance_scale: guidanceScale,
                        num_inference_steps: inferenceSteps,
                        seed: seed,
                        max_shift: maxShift,
                        base_shift: baseShift,
                        terminal: terminal
                    })
                });
                const data = await res.json();
                if (data.error) throw new Error(data.error);
                
                Notification.show("Video generation task created", "success");
                if (window.refreshTasks) window.refreshTasks();
                return;
            }

            const res = await fetch('/api/generate/podcast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    profiles, 
                    script, 
                    bgm_mood, 
                    ducking_level, 
                    eq_preset: eqPreset, 
                    reverb_level: reverbLevel,
                    stream: streamEnabled,
                    master_acx: masterAcx,
                    temperature: globalTemperature
                })
            });

            if (!res.ok) throw new Error("Podcast request failed");

            if (streamEnabled) {
                const reader = res.body.getReader();
                const player = document.getElementById('main-audio-player');
                const chunks = [];
                
                if (statusText) statusText.innerText = "Streaming Playback...";
                
                while(true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    chunks.push(value);
                    
                    if (chunks.length === 1) {
                        const blob = new Blob([value], { type: 'audio/wav' });
                        player.src = URL.createObjectURL(blob);
                        player.play();
                    }
                }
                if (statusText) statusText.innerText = "Stream Complete";
                return;
            }

            const data = await res.json();
            if (window.TaskPoller) {
                const blob = await window.TaskPoller.poll(data.task_id, (task) => {
                    if (statusText) statusText.innerText = `Producing: ${task.progress}% - ${task.message}`;
                });
                const url = URL.createObjectURL(blob);
                const player = document.getElementById('main-audio-player');
                if (player) { player.src = url; player.play(); }
                if (statusText) statusText.innerText = "Podcast Ready";
            }
        } catch (err) {
            if (statusText) statusText.innerText = "Production Failed";
            ErrorDisplay.show("Production Error", err.message);
        }
    },

    async exportStudioBundle() {
        const projectSelect = document.getElementById('project-select');
        const projectName = projectSelect.value;
        if (!projectName) return Notification.show("Select a project first", "warn");

        try {
            const resp = await fetch(`/api/projects/${projectName}/export`);
            if (!resp.ok) throw new Error("Export failed");
            const blob = await resp.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${projectName}_bundle.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            Notification.show("Bundle exported", "success");
        } catch (err) { Notification.show("Export failed", "error"); }
    },

    async suggestVideoScene() {
        const draftView = document.getElementById('canvas-draft-view');
        const productionView = document.getElementById('canvas-production-view');
        let textToAnalyze = "";

        if (productionView && productionView.style.display === 'flex' && window.CanvasManager.blocks.length > 0) {
            textToAnalyze = window.CanvasManager.blocks[0].text;
        } else {
            textToAnalyze = document.getElementById('script-editor').value.split('\n')[0];
        }

        if (!textToAnalyze) return Notification.show("Script is empty", "warn");

        try {
            const res = await fetch('/api/video/suggest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: textToAnalyze })
            });
            const data = await res.json();
            document.getElementById('video-prompt').value = data.suggestion;
            Notification.show("Suggestion generated", "success");
        } catch (err) {
            console.error("Suggestion failed:", err);
        }
    },

    async fetchProjectList() {
        const select = document.getElementById('project-select');
        if (!select) return;
        try {
            const res = await fetch('/api/projects');
            const data = await res.json();
            const current = select.value;
            select.innerHTML = '<option value="">(New)</option>' + 
                data.projects.map(p => `<option value="${p}" ${p === current ? 'selected' : ''}>${p}</option>`).join('');
        } catch (err) { console.error("Failed to fetch projects", err); }
    },

    async saveProject() {
        const select = document.getElementById('project-select');
        let name = select.value;
        if (!name) {
            name = prompt("Enter project name:");
            if (!name) return;
        }

        const data = {
            script_text: document.getElementById('script-editor').value,
            blocks: window.CanvasManager.blocks,
            settings: {
                bgm_mood: document.getElementById('bgm-select').value,
                ducking_level: parseFloat(document.getElementById('ducking-range').value) / 100.0,
                eq_preset: document.getElementById('audio-eq').value,
                reverb_level: parseFloat(document.getElementById('audio-reverb').value) / 100.0,
                global_temperature: parseFloat(document.getElementById('global-temperature').value),
                video_enabled: document.getElementById('video-enabled').checked,
                video_prompt: document.getElementById('video-prompt').value,
                master_acx: document.getElementById('master-acx').checked,
                video_max_shift: parseFloat(document.getElementById('video-max-shift').value) || null,
                video_base_shift: parseFloat(document.getElementById('video-base-shift').value) || null,
                video_terminal: parseFloat(document.getElementById('video-terminal').value) || null
            }
        };

        try {
            const res = await fetch(`/api/projects/${name}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!res.ok) throw new Error("Save failed");
            Notification.show("Project saved", "success");
            await this.fetchProjectList();
            select.value = name;
        } catch (err) { Notification.show("Save failed: " + err.message, "error"); }
    },

    async loadProject() {
        const name = document.getElementById('project-select').value;
        if (!name) return Notification.show("Select a project", "warn");

        try {
            const res = await fetch(`/api/projects/${name}`);
            if (!res.ok) throw new Error("Load failed");
            const data = await res.json();

            document.getElementById('script-editor').value = data.script_text || '';
            window.CanvasManager.blocks = data.blocks || [];
            
            if (data.settings) {
                document.getElementById('bgm-select').value = data.settings.bgm_mood || '';
                document.getElementById('ducking-range').value = (data.settings.ducking_level || 0) * 100;
                document.getElementById('ducking-val').innerText = `${Math.round((data.settings.ducking_level || 0) * 100)}%`;
                document.getElementById('audio-eq').value = data.settings.eq_preset || 'flat';
                document.getElementById('audio-reverb').value = (data.settings.reverb_level || 0) * 100;
                document.getElementById('reverb-val').innerText = `${Math.round((data.settings.reverb_level || 0) * 100)}%`;
                document.getElementById('global-temperature').value = data.settings.global_temperature || '0.9';
                document.getElementById('video-enabled').checked = data.settings.video_enabled || false;
                document.getElementById('video-prompt').value = data.settings.video_prompt || '';
                document.getElementById('video-options').style.display = data.settings.video_enabled ? 'block' : 'none';
                document.getElementById('master-acx').checked = data.settings.master_acx || false;
                document.getElementById('video-max-shift').value = data.settings.video_max_shift || '';
                document.getElementById('video-base-shift').value = data.settings.video_base_shift || '';
                document.getElementById('video-terminal').value = data.settings.video_terminal || '';
            }

            this.renderBlocks();
            Notification.show("Project loaded", "success");
        } catch (err) { Notification.show("Load failed: " + err.message, "error"); }
    },

    toggleCanvasView(view) {
        const draft = document.getElementById('canvas-draft-view');
        const prod = document.getElementById('canvas-production-view');
        if (!draft || !prod) return;

        if (view === 'draft') {
            draft.style.display = 'flex';
            prod.style.display = 'none';
            const heading = draft.querySelector('h1') || draft.querySelector('h2') || document.getElementById('script-editor');
            if (heading) heading.focus();
        } else {
            draft.style.display = 'none';
            prod.style.display = 'flex';
            this.renderBlocks();
            const heading = prod.querySelector('h1') || prod.querySelector('h2');
            if (heading) heading.focus();
        }
        localStorage.setItem('project_active_subtab', view);

        // Update buttons
        const container = document.querySelector('#projects-view .header');
        if (container) {
            container.querySelectorAll('button').forEach(btn => {
                const clickAttr = btn.getAttribute('onclick') || '';
                if (clickAttr.includes(`'${view}'`)) {
                    btn.classList.add('btn-primary');
                    btn.classList.remove('btn-secondary');
                    btn.setAttribute('aria-pressed', 'true');
                } else if (clickAttr.includes('toggleCanvasView')) {
                    btn.classList.add('btn-secondary');
                    btn.classList.remove('btn-primary');
                    btn.setAttribute('aria-pressed', 'false');
                }
            });
        }
    },

    loadSubTabState() {
        const saved = localStorage.getItem('project_active_subtab') || 'draft';
        this.toggleCanvasView(saved);
    },

    promoteToProduction() {
        const text = document.getElementById('script-editor').value;
        if (!text.trim()) return Notification.show("Draft is empty", "warn");

        const script = window.parseScript(text);
        window.CanvasManager.clear();
        script.forEach(s => window.CanvasManager.addBlock(s.role, s.text));
        
        this.toggleCanvasView('production');
        Notification.show("Promoted to production", "success");
    },

    renderBlocks() {
        const container = document.getElementById('blocks-container');
        if (!container) return;

        container.innerHTML = window.CanvasManager.blocks.map((b, index) => `
            <div class="card" 
                 draggable="true"
                 data-index="${index}"
                 data-id="${b.id}"
                 ondragstart="window.ProductionManager.handleDragStart(event)"
                 ondragover="window.ProductionManager.handleDragOver(event)"
                 ondragleave="window.ProductionManager.handleDragLeave(event)"
                 ondrop="window.ProductionManager.handleDrop(event)"
                 style="margin-bottom:12px; padding:16px; border-left:4px solid var(--accent); background:rgba(255,255,255,0.02); cursor:default;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <div class="drag-handle"><i class="fas fa-grip-vertical"></i></div>
                        <strong style="color:var(--accent); font-family:var(--font-mono);">${b.role.toUpperCase()}</strong>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-secondary btn-sm" onclick="window.CanvasManager.moveBlock('${b.id}', -1); window.ProductionManager.renderBlocks()" aria-label="Move block up" title="Move block up"><i class="fas fa-arrow-up" aria-hidden="true"></i></button>
                        <button class="btn btn-secondary btn-sm" onclick="window.CanvasManager.moveBlock('${b.id}', 1); window.ProductionManager.renderBlocks()" aria-label="Move block down" title="Move block down"><i class="fas fa-arrow-down" aria-hidden="true"></i></button>
                        <button class="btn btn-danger btn-sm" onclick="window.CanvasManager.deleteBlock('${b.id}'); window.ProductionManager.renderBlocks()" aria-label="Delete block" title="Delete block"><i class="fas fa-trash" aria-hidden="true"></i></button>
                    </div>
                </div>
                <div style="font-size:0.85rem; margin-bottom:12px; opacity:0.8; font-style:italic;">"${b.text.substring(0, 100)}${b.text.length > 100 ? '...' : ''}"</div>
                
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin-top:12px; border-top:1px solid rgba(255,255,255,0.05); padding-top:12px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span class="label-industrial" style="font-size:0.55rem; width:30px;">PAN</span>
                        <input type="range" min="-100" max="100" value="${(b.pan || 0) * 100}" style="flex:1; height:4px;" onchange="window.CanvasManager.updateBlock('${b.id}', {pan: this.value/100.0})">
                        <span class="volt-text" style="font-size:0.6rem; width:20px;">${b.pan > 0 ? 'R' : b.pan < 0 ? 'L' : 'C'}</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span class="label-industrial" style="font-size:0.55rem; width:30px;">TEMP</span>
                        <select class="btn btn-secondary btn-sm" style="flex:1; font-size:0.6rem; padding:2px;" onchange="window.CanvasManager.updateBlock('${b.id}', {temperature: parseFloat(this.value)})">
                            <option value="" ${b.temperature === undefined ? 'selected' : ''}>Auto</option>
                            <option value="0.9" ${b.temperature === 0.9 ? 'selected' : ''}>Creative</option>
                            <option value="0.5" ${b.temperature === 0.5 ? 'selected' : ''}>Balanced</option>
                            <option value="0.1" ${b.temperature === 0.1 ? 'selected' : ''}>Stable</option>
                        </select>
                    </div>
                </div>
            </div>
        `).join('');
    },

    handleDragStart(e) {
        e.dataTransfer.setData('text/plain', e.currentTarget.dataset.index);
        e.currentTarget.classList.add('block-dragging');
    },

    handleDragOver(e) {
        e.preventDefault();
        const card = e.currentTarget.closest('.card');
        if (card) card.classList.add('block-drag-over');
    },

    handleDragLeave(e) {
        const card = e.currentTarget.closest('.card');
        if (card) card.classList.remove('block-drag-over');
    },

    handleDrop(e) {
        e.preventDefault();
        const fromIndex = parseInt(e.dataTransfer.getData('text/plain'));
        const toIndex = parseInt(e.currentTarget.closest('.card').dataset.index);
        
        e.currentTarget.closest('.card').classList.remove('block-drag-over');
        document.querySelectorAll('.block-dragging').forEach(el => el.classList.remove('block-dragging'));

        if (fromIndex !== toIndex) {
            const blocks = window.CanvasManager.blocks;
            const movedBlock = blocks.splice(fromIndex, 1)[0];
            blocks.splice(toIndex, 0, movedBlock);
            this.renderBlocks();
            window.CanvasManager.save();
        }
    },

    filterProjects() {
        const query = document.getElementById('project-search').value.toLowerCase();
        const select = document.getElementById('project-select');
        const options = select.querySelectorAll('option');
        options.forEach(opt => {
            if (opt.value === "") return; // Don't filter placeholder
            const name = opt.innerText.toLowerCase();
            opt.style.display = name.includes(query) ? 'block' : 'none';
        });
    },

    async exportProject() {
        const select = document.getElementById('project-select');
        const name = select.value;
        if (!name) return Notification.show("Select or save a project first", "warn");
        
        const format = document.getElementById('export-format')?.value || 'wav';
        Notification.show(`Exporting ${name} as ${format.toUpperCase()}...`, "info");
        window.location.href = `/api/projects/${name}/export?format=${format}`;
    }
};
