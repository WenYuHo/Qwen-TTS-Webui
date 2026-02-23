import { state } from './state.js';
import { SpeakerStore, getAllProfiles, CanvasManager } from './store.js';
import { getVoicePreview } from './api.js';

export function renderAvatar(name, imageUrl) {
    if (imageUrl) {
        return `<img src="${imageUrl}" class="avatar" style="object-fit: cover;">`;
    }
    const initials = (name || "??").substring(0, 2).toUpperCase();
    return `<div class="avatar">${initials}</div>`;
}

export function switchView(view) {
    state.currentView = view;
    document.querySelectorAll('.view-container').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(v => v.classList.remove('active'));

    const viewEl = document.getElementById(`${view}-view`);
    if (viewEl) viewEl.classList.add('active');

    const navBtn = document.querySelector(`button[onclick="switchView('${view}')"]`);
    if (navBtn) navBtn.classList.add('active');

    // Special initialization for specific views
    if (view === 'speech') {
        renderSpeechVoiceList();
        renderVoiceLibrary();
    }
    if (view === 'dubbing') {
        renderS2STargetList();
    }
    if (view === 'system') {
        renderSystemView();
    }
    if (view === 'projects') {
        fetchProjects();
    }
}

export function renderSpeechVoiceList() {
    const selects = ['mix-voice-a', 'mix-voice-b', 'speech-voice', 's2s-target-voice'];
    const profiles = getAllProfiles();

    selects.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = '';
        profiles.forEach(p => {
            const opt = document.createElement('option');
            opt.value = JSON.stringify(p);
            opt.innerText = p.role;
            el.appendChild(opt);
        });
    });
}

export function renderS2STargetList() {
    const el = document.getElementById('s2s-target-voice');
    if (!el) return;
    el.innerHTML = '';
    getAllProfiles().forEach(p => {
        const opt = document.createElement('option');
        opt.value = JSON.stringify(p);
        opt.innerText = p.role;
        el.appendChild(opt);
    });
}

export function renderVoiceLibrary() {
    const grid = document.getElementById("voice-library-grid");
    if (!grid) return;
    grid.innerHTML = "";

    const voices = SpeakerStore.getVoices();
    voices.forEach(v => {
        const div = document.createElement("div");
        div.className = "card";
        div.style.padding = "20px";
        div.style.display = "flex";
        div.style.flexDirection = "column";
        div.style.gap = "16px";

        const escapedValue = (v.value || "").replace(/'/g, "\\'");

        div.innerHTML = `
            <div style="display:flex; align-items:center; gap:16px;">
                ${renderAvatar(v.name, v.image_url)}
                <div style="flex:1">
                    <h3 style="margin:0; font-size:1rem; font-weight:600;">${v.name}</h3>
                    <span class="badge">${v.type.toUpperCase()}</span>
                </div>
            </div>
            <div style="display:flex; gap:8px; border-top:1px solid var(--border); padding-top:12px;">
                <button class="btn btn-secondary btn-sm" style="flex:1" onclick="playVoicePreview('${v.name}', '${v.type}', '${escapedValue}')" title="Play Preview"><i class="fas fa-play"></i> Preview</button>
                <button class="btn btn-secondary btn-sm" onclick="document.getElementById('img-upload-${v.id}').click()" title="Change Image"><i class="fas fa-image"></i></button>
                <input type="file" id="img-upload-${v.id}" style="display:none" accept="image/*" onchange="uploadVoiceImage('${v.id}', this.files[0])">
                <button class="btn btn-secondary btn-sm" onclick="deleteVoice('${v.id}')" style="color:var(--danger)" title="Delete Voice"><i class="fas fa-trash"></i></button>
            </div>
        `;
        grid.appendChild(div);
    });
}

export function renderBlocks() {
    const container = document.getElementById('blocks-container');
    if (!container) return;
    container.innerHTML = '';
    CanvasManager.blocks.forEach(block => {
        const div = document.createElement('div');
        div.className = 'story-block';
        div.style.background = 'white';
        div.style.boxShadow = 'var(--shadow-sm)';

        div.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <div style="display:flex; align-items:center; gap:12px;">
                    ${renderAvatar(block.role)}
                    <span style="font-weight:600; font-size:0.9rem;">${block.role}</span>
                </div>
                <div style="display:flex; gap:12px; align-items:center;">
                    <select class="btn btn-secondary btn-sm" style="font-size:0.75rem; background:var(--bg-sidebar); border:none;" onchange="updateBlockProperty('${block.id}', 'language', this.value)">
                        <option value="auto" ${block.language === 'auto' ? 'selected' : ''}>Auto Detect</option>
                        <option value="en" ${block.language === 'en' ? 'selected' : ''}>English</option>
                        <option value="zh" ${block.language === 'zh' ? 'selected' : ''}>Chinese</option>
                        <option value="ja" ${block.language === 'ja' ? 'selected' : ''}>Japanese</option>
                        <option value="es" ${block.language === 'es' ? 'selected' : ''}>Spanish</option>
                    </select>
                    <div style="font-size:0.75rem; color:var(--text-secondary); display:flex; align-items:center; gap:6px;">
                        Pause: <input type="number" step="0.1" value="${block.pause_after}" style="width:50px; background:var(--bg-sidebar); border:none; border-radius:6px; padding:4px 8px; font-size:0.75rem;" onchange="updateBlockProperty('${block.id}', 'pause_after', this.value)">s
                    </div>
                    <button class="btn btn-secondary btn-sm" onclick="deleteBlock('${block.id}')" title="Remove"><i class="fas fa-times"></i></button>
                </div>
            </div>
            <p style="margin: 0 0 16px; color:var(--text-primary); line-height:1.6; font-size:1rem;">${block.text}</p>
            <div style="display:flex; align-items:center; gap:12px;">
                <button class="btn ${block.status === 'ready' ? 'btn-secondary' : 'btn-primary'} btn-sm" onclick="generateBlock('${block.id}')">
                    <i class="fas ${block.status === 'ready' ? 'fa-redo' : 'fa-magic'}"></i> ${block.status === 'ready' ? 'Regenerate' : 'Synthesize'}
                </button>
                ${block.audioUrl ? `<button class="btn btn-secondary btn-sm" onclick="playBlock('${block.id}')"><i class="fas fa-play"></i> Play Audio</button>` : ''}
                ${block.status === 'generating' ? `<div class="progress-container" style="flex:1; margin:0;"><div class="progress-bar" style="width: ${block.progress}%"></div></div>` : ''}
            </div>
        `;
        container.appendChild(div);
    });
}

// These are needed because switchView calls them but they might be defined elsewhere
// We will import them in the main app.js and assign them to window for now or export them here.
// I'll define placeholders or move the logic here.
import { fetchProjects } from './project.js';
import { renderSystemView } from './system.js';

export { fetchProjects, renderSystemView };
