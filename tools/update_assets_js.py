import sys

with open('src/static/app.js', 'r') as f:
    content = f.read()

# Replace loadAssets function with a more visually rich version
old_load = """async function loadAssets() {
    const grid = document.getElementById('asset-library-grid');
    if (!grid) return;
    grid.innerHTML = '<div class="card">Loading assets...</div>';

    try {
        const resp = await fetch('/api/assets/');
        const assets = await resp.json();

        if (assets.length === 0) {
            grid.innerHTML = '<div class="card">No assets uploaded yet.</div>';
            return;
        }

        grid.innerHTML = assets.map(asset => `
            <div class="card asset-card" style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <strong style="display:block;">${asset.name}</strong>
                    <span style="font-size:0.8rem; color:var(--text-secondary);">${(asset.size / 1024 / 1024).toFixed(2)} MB</span>
                </div>
                <div style="display:flex; gap:8px;">
                    <button class="btn btn-secondary btn-sm" onclick="playAsset('${asset.name}')"><i class="fas fa-play"></i></button>
                    <button class="btn btn-danger btn-sm" onclick="deleteAsset('${asset.name}')"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `).join('');

        // Update BGM selectors if they exist
        const bgmSelect = document.getElementById('bgm-select');
        if (bgmSelect) {
            const currentVal = bgmSelect.value;
            // Keep original presets
            const presets = ['mystery', 'tech', 'joy', 'rain'];
            bgmSelect.innerHTML = '<option value="">None</option>' +
                presets.map(p => `<option value="${p}" ${currentVal === p ? 'selected' : ''}>${p.charAt(0).toUpperCase() + p.slice(1)} (Preset)</option>`).join('') +
                assets.filter(a => a.name.endsWith('.mp3') || a.name.endsWith('.wav')).map(a =>
                    `<option value="${a.name}" ${currentVal === a.name ? 'selected' : ''}>${a.name} (Custom)</option>`
                ).join('');
        }

    } catch (err) {
        console.error("Failed to load assets", err);
        grid.innerHTML = '<div class="card">Error loading assets.</div>';
    }
}"""

new_load = """async function loadAssets() {
    const grid = document.getElementById('asset-library-grid');
    if (!grid) return;
    grid.innerHTML = '<div class="empty-state empty-state-grid"><h3>Loading assets...</h3></div>';

    try {
        const resp = await fetch('/api/assets/');
        const assets = await resp.json();

        if (assets.length === 0) {
            grid.innerHTML = `
                <div class="empty-state empty-state-grid" id="asset-drop-zone">
                    <i class="fas fa-cloud-upload-alt"></i>
                    <h3>No assets found</h3>
                    <p>Drag and drop files here or use the upload button above.</p>
                </div>
            `;
            setupDragAndDrop();
            return;
        }

        grid.innerHTML = assets.map(asset => {
            const isAudio = asset.name.endsWith('.mp3') || asset.name.endsWith('.wav');
            const icon = isAudio ? 'fa-file-audio' : 'fa-file';
            return `
                <div class="card asset-card" style="display:flex; align-items:center; gap:16px;">
                    <div class="asset-icon"><i class="fas ${icon}"></i></div>
                    <div style="flex:1;">
                        <strong style="display:block; font-size:0.95rem;">${asset.name}</strong>
                        <span style="font-size:0.8rem; color:var(--text-secondary);">${(asset.size / 1024 / 1024).toFixed(2)} MB</span>
                    </div>
                    <div style="display:flex; gap:8px;">
                        ${isAudio ? `<button class="btn btn-secondary btn-sm" onclick="playAsset('${asset.name}')" title="Play"><i class="fas fa-play"></i></button>` : ''}
                        <button class="btn btn-danger btn-sm" onclick="deleteAsset('${asset.name}')" title="Delete"><i class="fas fa-trash"></i></button>
                    </div>
                </div>
            `;
        }).join('');

        // Update BGM selectors if they exist
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

    } catch (err) {
        console.error("Failed to load assets", err);
        grid.innerHTML = '<div class="empty-state empty-state-grid"><h3>Error loading assets</h3></div>';
    }
}

function setupDragAndDrop() {
    const zone = document.getElementById('assets-view'); // Use entire view as zone
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
            uploadAsset(input);
        }
    });
}"""

content = content.replace(old_load, new_load)

# Add setupDragAndDrop call to the switchView logic
content = content.replace("if (view === 'assets') loadAssets();", "if (view === 'assets') { loadAssets(); setupDragAndDrop(); }")

with open('src/static/app.js', 'w') as f:
    f.write(content)
