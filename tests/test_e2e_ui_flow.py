import pytest
from playwright.sync_api import sync_playwright, expect

@pytest.mark.browser
def test_podcast_generation_flow(start_server):
    """Test the UI flow for creating a podcast project."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Mock the generation endpoint to avoid heavy computation
        def handle_generate(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body='{"task_id": "mock-task-123", "status": "pending", "message": "Mock generation started"}'
            )

        page.route("**/api/generate/podcast", handle_generate)
        
        page.goto("http://localhost:7860")
        
        # 1. Navigate to Project Studio
        page.click("#nav-projects")
        
        # 2. Ensure Draft view
        page.get_by_text("DRAFT", exact=True).click()
        
        # 3. Enter script
        editor = page.locator("#script-editor")
        editor.fill("Host: Welcome to the test podcast.")
        
        # 4. Click Produce and verify request
        produce_btn = page.get_by_text("PRODUCE FINAL")
        
        # Wait for the request to be initiated by the click
        with page.expect_request("**/api/generate/podcast") as request_info:
            produce_btn.click()
            
        request = request_info.value
        if request.method == "POST":
            post_data = request.post_data_json
            assert "script" in post_data
            assert post_data["script"][0]["role"] == "Host"
            assert post_data["script"][0]["text"] == "Welcome to the test podcast."
        
        browser.close()

@pytest.mark.browser
def test_video_generation_flow(start_server):
    """Test the UI flow for narrated video generation."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        def handle_video(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body='{"task_id": "mock-video-123", "status": "pending"}'
            )

        page.route("**/api/video/narrated", handle_video)
        
        page.goto("http://localhost:7860")
        page.click("#nav-projects")
        page.get_by_text("DRAFT", exact=True).click()
        
        # Enable Video
        page.check("#video-enabled")
        
        # Set Prompt
        page.fill("#video-prompt", "A futuristic city skyline")
        
        # Enter Script
        page.fill("#script-editor", "Narrator: In the year 3000...")
        
        # Trigger Generation and verify request
        with page.expect_request("**/api/video/narrated") as request_info:
            page.get_by_text("PRODUCE FINAL").click()
            
        request = request_info.value
        data = request.post_data_json
        
        assert data["prompt"] == "A futuristic city skyline"
        assert data["narration_text"] == "In the year 3000..."
        assert data["width"] == 768
        
        browser.close()
