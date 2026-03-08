import os
import sys
import time
import socket
import subprocess
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add src to python path for local imports if needed
src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

@pytest.fixture(scope="module", autouse=True)
def run_test_server():
    """Start the FastAPI server in the background for UI tests."""
    print("\nStarting background test server...")
    
    # Start the server as a subprocess
    server_process = subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=src_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the server to be ready (up to 30 seconds)
    start_time = time.time()
    server_ready = False
    
    while time.time() - start_time < 30:
        try:
            with socket.create_connection(("localhost", 8080), timeout=1):
                server_ready = True
                print("Test server is ready on port 8080.")
                break
        except OSError:
            time.sleep(1)
            
    if not server_ready:
        server_process.kill()
        out, err = server_process.communicate()
        pytest.fail(f"Test server failed to start on port 8080 in time.\nSTDOUT: {out}\nSTDERR: {err}")
        
    yield  # Run the tests
    
    # Teardown: stop the server
    print("\nStopping background test server...")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        print("Server termination timed out. Killing process...")
        server_process.kill()

@pytest.mark.browser
def test_voicelab_ui():
    """End-to-end browser smoke test for the VoiceLab UI."""
    with sync_playwright() as p:
        # 1. Launch Browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Listen for console messages
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
        
        try:
            # 2. Go to the app
            print("Navigating to http://localhost:8080...")
            page.goto("http://localhost:8080")
            page.wait_for_load_state("networkidle")
            
            # 3. Check if Voice Studio is active
            assert page.is_visible("#speech-view.active")
            
            # 4. Test Preset Metadata Rendering
            page.wait_for_selector(".voice-card", timeout=10000)
            presets = page.query_selector_all(".voice-card")
            assert len(presets) > 0
            
            card_text = presets[0].inner_text()
            assert "PRESET" in card_text.upper() or "|" in card_text
            
            # 5. Test Template Button
            page.click("text=DEEP MALE")
            prompt_val = page.input_value("#design-prompt")
            assert "authoritative" in prompt_val.lower()
            
            # 6. Test Design Preview Button (Background Task Trigger)
            page.click("text=DESIGN & PREVIEW")
            
            page.wait_for_selector("#design-preview-container", state="visible")
            status = page.inner_text("#design-status")
            assert status in ["Queuing...", "Processing...", "Ready"]
            
            # 7. Check Sidebar for Task (Persistent Progress)
            try:
                page.wait_for_selector(".task-item", timeout=15000)
                task_text = page.inner_text(".task-item")
                assert "SEGMENT" in task_text.upper() or "DESIGN" in task_text.upper()
            except Exception as e:
                html = page.inner_html(".js-task-monitor-list")
                print(f"DEBUG: Task monitor HTML: {html}")
                raise e
            
            # 8. Test Tab Switching Persistence
            page.click("#nav-projects")
            time.sleep(1) # transition
            assert page.is_visible("#projects-view.active")
            
            # Task should still be in the sidebar (or UI should at least not crash)
            assert page.is_visible(".sidebar")
            
            print("\n[PASS] UI TEST PASSED SUCCESSFULLY")
            
        except Exception as e:
            # Capture screenshot on failure for debugging
            page.screenshot(path="ui_test_failure.png")
            print(f"[FAIL] UI TEST FAILED: {e}")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    pytest.main(["-v", __file__])
