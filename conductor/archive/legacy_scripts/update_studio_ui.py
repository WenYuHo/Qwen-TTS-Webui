import sys

with open('src/static/index.html', 'r') as f:
    content = f.read()

# Group Advanced tools
old_section = """                        <span class="label">Production Settings</span>
                        <div class="control-group">
                            <label class="label" for="bgm-select">BGM Mood</label>
                            <select id="bgm-select">
                                <option value="">None</option>
                                <option value="mystery">Mystery</option>
                                <option value="tech">Tech</option>
                                <option value="joy">Joyful</option>
                                <option value="rain">Rain</option>
                            </select>
                        </div>
                        <div class="control-group">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <label class="label" for="ducking-range">Auto-Ducking</label>
                                <span id="ducking-val" style="font-size:0.8rem; opacity:0.7;">0%</span>
                            </div>
                            <input type="range" id="ducking-range" min="0" max="100" value="0" style="width:100%" oninput="document.getElementById('ducking-val').innerText = this.value + '%' ">
                        </div>"""

new_section = """                        <span class="label">Production Settings</span>
                        <div class="card" style="padding:16px; background:rgba(0,0,0,0.1); margin-bottom:24px;">
                            <div class="control-group" style="margin-bottom:16px;">
                                <label class="label" for="bgm-select">BGM Mood</label>
                                <select id="bgm-select">
                                    <option value="">None</option>
                                    <option value="mystery">Mystery</option>
                                    <option value="tech">Tech</option>
                                    <option value="joy">Joyful</option>
                                    <option value="rain">Rain</option>
                                </select>
                            </div>
                            <div class="control-group" style="margin-bottom:0;">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <label class="label" for="ducking-range" title="Automatically lowers BGM volume when characters are speaking">Auto-Ducking <i class="fas fa-info-circle" style="opacity:0.5;"></i></label>
                                    <span id="ducking-val" style="font-size:0.8rem; opacity:0.7;">0%</span>
                                </div>
                                <input type="range" id="ducking-range" min="0" max="100" value="0" style="width:100%" oninput="document.getElementById('ducking-val').innerText = this.value + '%' ">
                            </div>
                        </div>"""

content = content.replace(old_section, new_section)

with open('src/static/index.html', 'w') as f:
    f.write(content)
