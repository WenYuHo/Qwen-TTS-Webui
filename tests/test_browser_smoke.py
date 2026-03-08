import pytest
from playwright.sync_api import sync_playwright

@pytest.mark.browser
def test_homepage_loads(start_server):
    """Verify all tabs render without JS errors."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        try:
            page.goto("http://localhost:7860")
            
            # 1. Verify Voice Studio (default view)
            assert page.locator("#voice-library-grid").is_visible(timeout=5000)
            
            # 2. Navigate to Project Studio
            page.click("#nav-projects")
            
            # Ensure Draft view is active
            page.get_by_text("DRAFT", exact=True).click()

            # 3. Verify Project Studio elements
            assert page.locator("#script-editor").is_visible(timeout=5000)
            
            assert len(errors) == 0, f"JS errors: {errors}"
        finally:
            browser.close()
