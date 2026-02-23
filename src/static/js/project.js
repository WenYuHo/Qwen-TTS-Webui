import { TaskMonitor } from './tasks.js';
import { CanvasManager, getAllProfiles, parseScript, SpeakerStore } from './store.js';
import { renderBlocks, switchView } from './ui.js';
import { TaskPoller } from './api.js';

export async function fetchProjects() {
    const select = document.getElementById('project-select');
    if (!select) return;
    try {
        const res = await fetch('/api/projects');
        const data = await res.json();
        select.innerHTML = '<option value="">(New Project)</option>';
        data.projects.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p; opt.innerText = p; select.appendChild(opt);
        });
    } catch (e) { console.error(e); }
}

export async function saveProject() {
    let name = document.getElementById('project-select').value || prompt("Project Name:");
    if (!name) return;
    const data = {
        name,
        blocks: CanvasManager.blocks.map(b => ({ id: b.id, role: b.role, text: b.text, status: b.status, language: b.language, pause_after: b.pause_after })),
        script_draft: document.getElementById('script-editor').value,
        voices: SpeakerStore.getVoices()
    };
    try {
        await fetch(`/api/projects/${name}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        alert("Saved!"); fetchProjects();
    } catch (e) { alert(e.message); }
}

export async function loadProject() {
    const name = document.getElementById('project-select').value;
    if (!name) return;
    try {
        const res = await fetch(`/api/projects/${name}`);
        const data = await res.json();
        document.getElementById('script-editor').value = data.script_draft || "";
        CanvasManager.clear();
        (data.blocks || []).forEach(b => { CanvasManager.blocks.push({ ...b, audioUrl: null }); });
        renderBlocks();
        alert("Loaded!");
    } catch (e) { alert(e.message); }
}

export async function promoteToProduction() {
    const script = parseScript(document.getElementById('script-editor').value);
    if (script.length === 0) return alert("Write script first (e.g., [Alice]: Hello)");
    CanvasManager.clear();
    script.forEach(line => CanvasManager.addBlock(line.role, line.text));
    CanvasManager.save();
    renderBlocks();
    switchView('production'); // This might need to be fixed as there is no 'production' view, just 'projects' with a tab
    // Wait, switchView in my code handles draft/production tabs differently.
    // toggleCanvasView handles the tabs.
}

export function toggleCanvasView(view) {
    document.getElementById('canvas-draft-view').style.display = view === 'draft' ? 'flex' : 'none';
    document.getElementById('canvas-production-view').style.display = view === 'production' ? 'flex' : 'none';
    if (view === 'production') renderBlocks();
}

export async function generateBlock(id) {
    const block = CanvasManager.blocks.find(b => b.id === id);
    if (!block) return;
    block.status = 'generating'; block.progress = 0; renderBlocks();
    const profiles = getAllProfiles();
    try {
        const res = await fetch('/api/generate/segment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profiles: profiles,
                script: [{ role: block.role, text: block.text, language: block.language }]
            })
        });
        const { task_id } = await res.json();
        TaskMonitor.addTask(task_id, 'segment');
        const blob = await TaskPoller.poll(task_id, (task) => {
            block.progress = task.progress;
            renderBlocks();
        });
        block.audioUrl = URL.createObjectURL(blob);
        block.status = 'ready';
        renderBlocks();
    } catch (e) { block.status = 'error'; renderBlocks(); alert(e.message); }
}

export function playBlock(id) {
    const block = CanvasManager.blocks.find(b => b.id === id);
    if (block && block.audioUrl) {
        const player = document.getElementById('main-audio-player');
        player.src = block.audioUrl;
        player.play();
    }
}

export function deleteBlock(id) { CanvasManager.deleteBlock(id); renderBlocks(); }

export async function generatePodcast(btn) {
    const script = CanvasManager.blocks.map(b => ({ role: b.role, text: b.text, language: b.language, pause_after: b.pause_after }));
    if (script.length === 0) return alert("Empty script.");
    const profiles = getAllProfiles();
    const bgm = document.getElementById('bgm-select').value;
    const statusText = document.getElementById('status-text');

    if (btn) btn.disabled = true;
    statusText.innerText = "Producing podcast...";

    try {
        const res = await fetch('/api/generate/podcast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profiles, script, bgm_mood: bgm })
        });
        const { task_id } = await res.json();
        TaskMonitor.addTask(task_id, 'segment');
        const blob = await TaskPoller.poll(task_id, (task) => { statusText.innerText = `Producing: ${task.progress}%`; });
        const player = document.getElementById('main-audio-player');
        player.src = URL.createObjectURL(blob);
        player.play();
        statusText.innerText = 'Ready';
    } catch (e) { alert(e.message); statusText.innerText = "Failed"; }
    finally { if (btn) btn.disabled = false; }
}

export async function batchSynthesize() {
    for (let block of CanvasManager.blocks) {
        if (block.status !== 'ready') await generateBlock(block.id);
    }
}

export async function generateVideo(btn) {
    const projectName = document.getElementById("project-select").value;
    if (!projectName) return alert("Please save/select a project first.");

    const aspectRatio = document.getElementById("video-aspect").value;
    const includeSubtitles = document.getElementById("video-subtitles").checked;
    const font_size = parseInt(document.getElementById("video-font-size").value) || 40;
    const font_type = document.getElementById("video-font-type").value || "DejaVuSans-Bold.ttf";
    const statusText = document.getElementById("status-text");

    if (btn) btn.disabled = true;
    statusText.innerText = "Generating Video (this takes time)...";
    try {
        await saveProject();

        const res = await fetch("/api/generate/video", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                project_name: projectName,
                aspect_ratio: aspectRatio,
                include_subtitles: includeSubtitles,
                font_size: font_size,
                font_type: font_type,
                bgm_mood: document.getElementById("bgm-select").value
            })
        });
        const { task_id } = await res.json();
        TaskMonitor.addTask(task_id, 'segment');
        const blob = await TaskPoller.poll(task_id, (task) => {
            statusText.innerText = `Video: ${task.progress}% - ${task.message}`;
        });

        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${projectName}_video.mp4`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        statusText.innerText = "Video Generation Complete! Download started.";
    } catch (e) { alert(e.message); statusText.innerText = "Video failed"; }
    finally { if (btn) btn.disabled = false; }
}

export function updateBlockProperty(id, prop, val) {
    const block = CanvasManager.blocks.find(b => b.id === id);
    if (block) {
        block[prop] = prop === 'pause_after' ? parseFloat(val) : val;
        CanvasManager.save();
    }
}
