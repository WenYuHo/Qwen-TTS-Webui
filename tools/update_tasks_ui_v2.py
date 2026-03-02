import sys

with open('src/static/index.html', 'r') as f:
    content = f.read()

# Add clear button to Task Monitor
old_header = '<h2 style="font-size: 1.1rem;">Live Task Monitor</h2>'
new_header = """<div style="display:flex; align-items:center; gap:12px;">
                            <h2 style="font-size: 1.1rem;">Live Task Monitor</h2>
                            <button class="btn btn-secondary btn-sm" onclick="clearCompletedTasks()" style="padding: 4px 8px; font-size: 0.7rem;"><i class="fas fa-broom"></i> Clear Finished</button>
                        </div>"""

if 'clearCompletedTasks' not in content:
    content = content.replace(old_header, new_header)

with open('src/static/index.html', 'w') as f:
    f.write(content)
