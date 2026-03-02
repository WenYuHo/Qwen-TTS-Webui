// --- Production & Studio Module ---

export const ProductionManager = {
    async generatePodcast() {
        const statusText = document.getElementById('status-badge');
        const bgm_mood = document.getElementById('bgm-select').value;
        const ducking_level = parseFloat(document.getElementById('ducking-range').value) / 100.0;
        
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

        const productionView = document.getElementById('canvas-production-view');
        const isProduction = productionView && productionView.style.display === 'flex';

        let script = [];
        if (isProduction) {
            script = window.CanvasManager.blocks.map(b => ({
                role: b.role,
                text: b.text,
                language: b.language || 'auto',
                pause_after: b.pause_after || 0.5
            }));
        } else {
            script = window.parseScript(document.getElementById('script-editor').value);
        }

        if (script.length === 0) return alert("Script is empty.");
        const profiles = window.getAllProfiles();

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
                        seed: seed
                    })
                });
                const data = await res.json();
                if (data.error) throw new Error(data.error);
                
                alert("Video generation task created. Check the Task List.");
                if (window.refreshTasks) window.refreshTasks();
                return;
            }

            const res = await fetch('/api/generate/podcast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profiles, script, bgm_mood, ducking_level })
            });
            if (!res.ok) throw new Error("Podcast request failed");
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
            alert(`Error: ${err.message}`);
        }
    },

    async exportStudioBundle() {
        const projectSelect = document.getElementById('project-select');
        const projectName = projectSelect.value;
        if (!projectName) return alert("Please select and save a project first.");

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
        } catch (err) { alert(`Failed to export bundle: ${err.message}`); }
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

        if (!textToAnalyze) return alert("Write some script first to get a suggestion.");

        try {
            const res = await fetch('/api/video/suggest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: textToAnalyze })
            });
            const data = await res.json();
            document.getElementById('video-prompt').value = data.suggestion;
        } catch (err) {
            console.error("Suggestion failed:", err);
        }
    }
};
