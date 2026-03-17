// --- Asset Management Module ---
import { Notification } from './ui_components.js';
import { escapeHTML } from './shared.js';

export const AssetManager = {
    async loadAssets() {
        const grid = document.getElementById('asset-library-grid');
        if (!grid) return;
        grid.innerHTML = '<div class="empty-state empty-state-grid"><h3><i class="fas fa-spinner fa-spin"></i> Loading assets...</h3></div>';

        try {
            const resp = await fetch('/api/assets/');
            const assets = await resp.json();

            if (assets.length === 0) {
                grid.innerHTML = `
                    <div class="empty-state empty-state-grid">
                        <i class="fas fa-cloud-upload-alt"></i>
                        <h3>No assets found</h3>
                        <p>Drag and drop files here or use the upload button above.</p>
                    </div>
                `;
                return;
            }

            grid.innerHTML = assets.map(asset => {
                const isAudio = asset.name.endsWith('.mp3') || asset.name.endsWith('.wav');
                const icon = isAudio ? 'fa-file-audio' : 'fa-file';
                return `
                    <div class="card asset-card" style="display:flex; align-items:center; gap:16px;">
                        <div class="asset-icon" aria-hidden="true"><i class="fas ${icon}"></i></div>
                        <div style="flex:1;">
                            <strong style="display:block; font-size:0.95rem;">${asset.name}</strong>
                            <span style="font-size:0.8rem; color:var(--text-secondary);">${(asset.size / 1024 / 1024).toFixed(2)} MB</span>
                        </div>
                        <div style="display:flex; gap:8px;">
                            ${isAudio ? `<button class="btn btn-secondary btn-sm" onclick="playAsset('${asset.name}', this)" title="Play ${asset.name}" aria-label="Play ${asset.name}"><i class="fas fa-play" aria-hidden="true"></i></button>` : ''}
                            <button class="btn btn-danger btn-sm" onclick="deleteAsset('${asset.name}')" title="Delete ${asset.name}" aria-label="Delete ${asset.name}"><i class="fas fa-trash" aria-hidden="true"></i></button>
                        </div>
                    </div>
                `;
            }).join('');

            // Update BGM selectors
            const bgmSelect = document.getElementById('bgm-select');
            if (bgmSelect) {
                const currentVal = bgmSelect.value;
                const presets = ['mystery', 'tech', 'joy', 'rain'];
                bgmSelect.innerHTML = '<option value="">None</option>' +
                    presets.map(p => `<option value="${p}" ${currentVal === p ? 'selected' : ''}>${p.charAt(0).toUpperCase() + p.slice(1)} (Preset)</option>`).join('') +
                    assets.filter(a => a.name.endsWith('.mp3') || a.name.endsWith('.wav')).map(a =>
                        `<option value="${a.name}" ${currentVal === a.name ? 'selected' : ''}>${a.name} (Custom)</option>`
                    ).join('');
            }
            this.filterAssets();
        } catch (err) {
            console.error("Failed to load assets", err);
            grid.innerHTML = '<div class="empty-state empty-state-grid"><h3>Error loading assets</h3></div>';
        }
    },

    setupDragAndDrop() {
        const zone = document.getElementById('assets-view');
        if (!zone) return;

        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('drag-over');
        });

        ['dragleave', 'dragend', 'drop'].forEach(evt => {
            zone.addEventListener(evt, () => zone.classList.remove('drag-over'));
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const input = { files: files };
                this.uploadAsset(input);
            }
        });
    },

    async uploadAsset(input) {
        if (!input.files || input.files.length === 0) return;
        const file = input.files[0];
        const formData = new FormData();
        formData.append('file', file);

        try {
            const resp = await fetch('/api/assets/upload', { method: 'POST', body: formData });
            if (resp.ok) {
                this.loadAssets();
                Notification.show("Asset uploaded", "success");
            } else Notification.show("Upload failed", "error");
        } catch (err) { console.error("Upload error", err); }
    },

    async deleteAsset(name) {
        if (!confirm(`Delete ${name}?`)) return;
        try {
            const resp = await fetch(`/api/assets/${name}`, { method: 'DELETE' });
            if (resp.ok) {
                this.loadAssets();
                Notification.show("Asset deleted", "success");
            }
        } catch (err) { console.error("Delete error", err); }
    },

    async playAsset(name, btn) {
        const player = document.getElementById('preview-player');
        if (!player) return;

        const originalHtml = btn ? btn.innerHTML : null;
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        }

        try {
            const url = `/api/assets/download/${name}`;
            player.src = url;
            await player.play();
        } catch (err) {
            console.error("Playback failed", err);
            Notification.show("Playback failed", "error");
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        }
    },

    filterAssets() {
        const query = document.getElementById('asset-search').value.toLowerCase();
        const grid = document.getElementById('asset-library-grid');
        if (!grid) return;
        const cards = grid.querySelectorAll('.asset-card');
        let visibleCount = 0;

        cards.forEach(card => {
            const name = card.querySelector('strong')?.innerText.toLowerCase() || '';
            const isVisible = name.includes(query);
            card.style.display = isVisible ? 'flex' : 'none';
            if (isVisible) visibleCount++;
        });

        // Handle empty search results
        let emptySearch = grid.querySelector('.empty-search-state');
        if (visibleCount === 0 && query !== '') {
            if (!emptySearch) {
                emptySearch = document.createElement('div');
                emptySearch.className = 'empty-state empty-state-grid empty-search-state';
                emptySearch.innerHTML = `
                    <i class="fas fa-search"></i>
                    <h3>No assets match "${escapeHTML(query)}"</h3>
                    <p>Try a different search term.</p>
                `;
                grid.appendChild(emptySearch);
            } else {
                emptySearch.querySelector('h3').textContent = `No assets match "${query}"`;
                emptySearch.style.display = 'block';
            }
        } else if (emptySearch) {
            emptySearch.style.display = 'none';
        }
    }
};
