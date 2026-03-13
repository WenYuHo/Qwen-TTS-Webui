import pytest
from src.backend.api.generation import parse_script_with_emotions

def test_parse_script_with_emotions_simple():
    """Verify that [happy] tag is extracted and mapped to instruct."""
    script_text = "[Alice]\n[happy] Hello everyone!"
    blocks = parse_script_with_emotions(script_text)
    
    assert len(blocks) == 1
    assert blocks[0]["role"] == "Alice"
    assert "happy" not in blocks[0]["text"]
    assert "cheerful" in blocks[0]["instruct"]

def test_parse_script_with_emotions_multiple():
    """Verify multiple speakers and emotions."""
    script_text = """
    [Alice]
    [happy] I am so glad to see you!
    
    [Bob]
    [serious] We have important matters to discuss.
    """
    blocks = parse_script_with_emotions(script_text)
    
    assert len(blocks) == 2
    assert blocks[0]["role"] == "Alice"
    assert "cheerful" in blocks[0]["instruct"]
    
    assert blocks[1]["role"] == "Bob"
    assert "authoritative" in blocks[1]["instruct"]

def test_parse_script_no_emotions():
    """Verify backward compatibility with no tags."""
    script_text = "[Alice]\nJust a regular sentence."
    blocks = parse_script_with_emotions(script_text)
    
    assert len(blocks) == 1
    assert blocks[0]["role"] == "Alice"
    assert blocks[0]["text"] == "Just a regular sentence."
    assert blocks[0].get("instruct") is None
