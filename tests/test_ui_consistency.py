import os

def test_ui_files_exist():
    assert os.path.exists("src/static/index.html")
    assert os.path.exists("src/static/style.css")
    assert os.path.exists("src/static/app.js")

def test_index_html_contains_new_elements():
    with open("src/static/index.html", "r") as f:
        content = f.read()
    assert 'id="assets-view"' in content
    assert 'Asset Library' in content
    assert 'ACTIVE TASKS' in content
    assert 'id="ducking-range"' in content
    assert 'aria-label="Global preview player"' in content
    assert 'aria-label="Close video preview"' in content

def test_style_css_contains_new_styles():
    with open("src/static/style.css", "r") as f:
        content = f.read()
    assert ".brutalist-overlay" in content
    assert ".nav-item.active" in content
    assert "font-family: var(--font-display)" in content
    assert "*:focus-visible" in content

def test_app_js_contains_new_functions():
    with open("src/static/app.js", "r") as f:
        content = f.read()
    assert 'loadAssets: AssetManager.loadAssets' in content
    assert 'playAsset: AssetManager.playAsset' in content
    assert 'setupDragAndDrop: AssetManager.setupDragAndDrop' in content
    assert 'refreshTasks: TaskManager.refreshTasks' in content
    assert 'generatePodcast: ProductionManager.generatePodcast' in content
