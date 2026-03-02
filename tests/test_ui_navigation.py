import pytest
from playwright.sync_api import sync_playwright, expect
import time

def test_studio_navigation():
    """Verify that a human can navigate through all major Studio views."""
    with sync_playwright() as p:
        # 1. Launch Browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_context().new_page()
        
        # Capture console messages
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.type} {msg.text}"))
        page.on("pageerror", lambda err: print(f"BROWSER ERROR: {err}"))
        
        # 2. Go to App (Assumes server is running on 8080)
        url = "http://localhost:8080"
        try:
            page.goto(url, timeout=10000)
        except Exception:
            pytest.skip("Local Studio server not running on localhost:8080. Start studio.bat first.")

        # 3. Verify Page Title
        expect(page).to_have_title("Qwen-TTS Podcast Studio")
        
        # 4. Navigate to Project Studio
        print("Clicking 'Project Studio' sidebar button...")
        page.click("#nav-projects", force=True)
        
        # Wait for the old view to exit and new to become active
        try:
            # We wait for the 'active' class to appear on the projects-view
            page.wait_for_selector("#projects-view.active", timeout=5000)
            print("[OK] Project Studio is now active.")
        except Exception as e:
            page.screenshot(path="debug_ui_failure_nav.png")
            print(f"[FAIL] Navigation failed. Screenshot saved.")
            raise
        expect(page.locator("#projects-view h1")).to_contain_text("PROJECT STUDIO")

        # 5. Navigate to System
        print("Clicking 'System'...")
        page.click("#nav-system", force=True)
        time.sleep(0.5)
        expect(page.locator("#system-view")).to_be_visible()
        
        # 6. Test Help Modal
        print("Testing Help Modal...")
        page.click("#system-view button:has-text('HELP')")
        help_modal = page.locator(".modal-overlay:has-text('COMMAND REFERENCE')")
        expect(help_modal).to_be_visible()
        expect(help_modal).to_contain_text("COMMAND REFERENCE")
        
        # 7. Close Modal
        page.click("button:has-text('ACKNOWLEDGE')")
        expect(help_modal).not_to_be_visible()

        # 8. Return to Voice Studio and verify components
        print("Returning to Voice Studio and verifying components...")
        page.click("#nav-speech", force=True)
        expect(page.locator("#speech-view")).to_be_visible()
        expect(page.locator("h2:has-text('Voice Design')")).to_be_visible()
        expect(page.locator("h2:has-text('Voice Cloning')")).to_be_visible()
        expect(page.locator("h2:has-text('Voice Mixer')")).to_be_visible()
        expect(page.locator("#voice-library-grid")).to_be_visible()

        # 9. Test Dubbing View
        print("Testing Dubbing & S2S view...")
        page.click("#nav-dubbing", force=True)
        expect(page.locator("#dubbing-view")).to_be_visible()
        expect(page.locator("h2:has-text('Dubbing (Translation)')")).to_be_visible()
        expect(page.locator("h2:has-text('Voice Changer (S2S)')")).to_be_visible()
        
        browser.close()

if __name__ == "__main__":
    test_studio_navigation()
