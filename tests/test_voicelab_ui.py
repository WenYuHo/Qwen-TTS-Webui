import os
import time
import pytest
from playwright.sync_api import sync_playwright

def test_voicelab_ui():
    with sync_playwright() as p:
        # 1. Launch Browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # ⚡ Bolt: Listen for console messages
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
        
        try:
            # 2. Go to the app
            print("Navigating to http://localhost:8080...")
            page.goto("http://localhost:8080")
            page.wait_for_load_state("networkidle")
            
            # 3. Check if Voice Studio is active
            print("Checking Voice Studio view...")
            assert page.is_visible("#speech-view.active")
            
            # 4. Test Preset Metadata Rendering
            print("Verifying Preset Library is loaded...")
            # Wait for presets to load from API
            page.wait_for_selector(".voice-card")
            presets = page.query_selector_all(".voice-card")
            print(f"Found {len(presets)} voice cards.")
            assert len(presets) > 0
            
            # Check for one of our new metadata fields
            card_text = presets[0].inner_text()
            print(f"First card content: {card_text}")
            # The metadata we added in voices.py includes "Male" or "Female" and descriptions
            assert "PRESET" in card_text.upper() or "|" in card_text
            
            # 5. Test Template Button
            print("Testing 'DEEP MALE' template button...")
            page.click("text=DEEP MALE")
            prompt_val = page.input_value("#design-prompt")
            print(f"Prompt value after click: {prompt_val}")
            assert "authoritative" in prompt_val.lower()
            
            # 6. Test Design Preview Button (Background Task Trigger)
            print("Triggering DESIGN & PREVIEW...")
            # We updated testVoiceDesign to disable the button and show "Queuing..."
            page.click("text=DESIGN & PREVIEW")
            
            # Wait for the design container to appear
            page.wait_for_selector("#design-preview-container", state="visible")
            status = page.inner_text("#design-status")
            print(f"Design status: {status}")
            assert status in ["Queuing...", "Processing...", "Ready"]
            
            # 7. Check Sidebar for Task (Persistent Progress)
            print("Checking Sidebar for background task...")
            # Increase timeout for CPU generation
            try:
                page.wait_for_selector(".task-item", timeout=60000)
                task_text = page.inner_text(".task-item")
                print(f"Found task in sidebar: {task_text}")
                assert "SEGMENT" in task_text.upper()
            except Exception as e:
                # Log the current HTML of the task monitor for debugging
                html = page.inner_html(".js-task-monitor-list")
                print(f"DEBUG: Task monitor HTML: {html}")
                raise e
            
            # 8. Test Tab Switching Persistence
            print("Testing tab switching persistence...")
            page.click("#nav-projects")
            time.sleep(1) # transition
            assert page.is_visible("#projects-view.active")
            
            # Task should still be in the sidebar
            assert page.is_visible(".task-item")
            print("✅ Task persists across view switches.")
            
            print("\n✅ UI TEST PASSED SUCCESSFULLY")
            
        except Exception as e:
            # Capture screenshot on failure for debugging
            page.screenshot(path="ui_test_failure.png")
            print(f"❌ UI TEST FAILED: {e}")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    test_voicelab_ui()
