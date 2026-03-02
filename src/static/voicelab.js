// --- Voice Lab (Design, Clone, Mix) Module ---
import { TaskManager } from './task_manager.js';
import { Notification, ErrorDisplay } from './ui_components.js';

export const VoiceLabManager = {
    async testVoiceDesign(btn) {
        const prompt = document.getElementById('design-prompt').value;
        if (!prompt) return Notification.show("Enter a style prompt", "warn");

        const container = document.getElementById('design-preview-container');
        const status = document.getElementById('design-status');
        const player = document.getElementById('preview-player');

        container.style.display = 'block';
        status.innerText = "Designing...";
        btn.disabled = true;

        try {
            // ... res fetch ...
            if (!res.ok) throw new Error("Design preview failed");
            // ... reader loop ...
            Notification.show("Design preview ready", "success");
        } catch (err) {
            status.innerText = "Error";
            ErrorDisplay.show("Design Error", err.message);
            console.error(err);
        } finally {
            btn.disabled = false;
        }
    },
...
        try {
            // ... upRes and upData ...
            if (!res.ok) throw new Error("Clone preview failed");
            // ... reader loop ...
            Notification.show("Clone preview ready", "success");
        } catch (err) {
            status.innerText = "Error";
            ErrorDisplay.show("Cloning Error", err.message);
            console.error(err);
        } finally {
            btn.disabled = false;
        }
    },
...
        try {
            // ... res fetch ...
            if (!res.ok) throw new Error("Mix preview failed");
            // ... reader loop ...
            Notification.show("Mix preview ready", "success");
        } catch (err) {
            status.innerText = "Error";
            ErrorDisplay.show("Mixing Error", err.message);
            console.error(err);
        } finally {
            btn.disabled = false;
        }
    },

    playDesignPreview() {
        const player = document.getElementById('preview-player');
        if (window.state.voicelab.lastDesignedPath) {
            player.src = window.state.voicelab.lastDesignedPath;
            player.play();
        }
    },

    playClonePreview() {
        const player = document.getElementById('preview-player');
        if (window.state.voicelab.lastClonedPath) {
            player.src = window.state.voicelab.lastClonedPath;
            player.play();
        }
    },

    playMixPreview() {
        const player = document.getElementById('preview-player');
        if (window.state.voicelab.lastMixedPath) {
            player.src = window.state.voicelab.lastMixedPath;
            player.play();
        }
    },

    filterVoiceLibrary() {
        const query = document.getElementById('voice-search').value.toLowerCase();
        const cards = document.querySelectorAll('#voice-library-grid .voice-card');
        cards.forEach(card => {
            const name = card.querySelector('strong')?.innerText.toLowerCase() || '';
            card.style.display = name.includes(query) ? 'flex' : 'none';
        });
    }
};
