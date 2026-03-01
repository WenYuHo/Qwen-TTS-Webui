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
    assert 'Live Task Monitor' in content
    assert 'Export Bundle' in content
    assert 'id="ducking-range"' in content

def test_style_css_contains_new_styles():
    with open("src/static/style.css", "r") as f:
        content = f.read()
    assert ".brutalist-overlay" in content
    assert ".nav-item.active" in content
    assert "font-family: var(--font-display)" in content

def test_app_js_contains_new_functions():
    with open("src/static/app.js", "r") as f:
        content = f.read()
    assert 'async function loadAssets()' in content
    assert 'function setupDragAndDrop()' in content
    assert 'async function refreshTasks()' in content
    assert 'async function exportStudioBundle()' in content
    assert 'async function generatePodcast()' in content
