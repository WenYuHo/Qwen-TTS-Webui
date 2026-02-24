import pytest
import numpy as np
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Mock model_loader.get_model to prevent actual model loading
with patch("backend.model_loader._ensure_qwen_tts"):
    from backend.podcast_engine import PodcastEngine


def test_engine_initialization():
    engine = PodcastEngine()
    assert not hasattr(engine, "speaker_profiles")


def test_generate_podcast_empty_script():
    engine = PodcastEngine()
    result = engine.generate_podcast([], profiles={})
    assert result is None


def test_generate_podcast_with_mocked_segment(monkeypatch):
    """Generate podcast concatenates segments with padding."""
    engine = PodcastEngine()
    dummy_wav = np.zeros(24000, dtype=np.float32)
    monkeypatch.setattr(engine, "generate_segment", lambda text, profile, **kwargs: (dummy_wav, 24000))

    script = [{"role": "ryan", "text": "Hello"}]
    profiles = {"ryan": {"type": "preset", "value": "Ryan"}}
    result = engine.generate_podcast(script, profiles=profiles)

    assert result is not None
    assert "waveform" in result
    assert result["sample_rate"] == 24000
    # 1s (dummy) + 2s (padding) = 3s = 72000 samples
    assert len(result["waveform"]) == 72000


def test_generate_podcast_missing_bgm_should_not_crash(monkeypatch):
    """Engine proceeds with voice generation even if BGM file is missing."""
    engine = PodcastEngine()
    dummy_wav = np.zeros(24000, dtype=np.float32)
    monkeypatch.setattr(engine, "generate_segment", lambda text, profile, **kwargs: (dummy_wav, 24000))

    script = [{"role": "Ryan", "text": "Hello"}]
    profiles = {"Ryan": {"type": "preset", "value": "Ryan"}}
    result = engine.generate_podcast(script, profiles=profiles, bgm_mood="non_existent_mood_12345")

    assert result is not None
    assert "waveform" in result
    assert result["sample_rate"] == 24000


def test_normalization(monkeypatch):
    """Audio with values > 1.0 should be normalized to prevent clipping."""
    engine = PodcastEngine()
    clipping_wav = np.array([2.0, -1.5, 0.0], dtype=np.float32)
    monkeypatch.setattr(engine, "generate_segment", lambda text, profile, **kwargs: (clipping_wav, 24000))

    script = [{"role": "Ryan", "text": "Hello"}]
    profiles = {"Ryan": {"type": "preset", "value": "Ryan"}}
    result = engine.generate_podcast(script, profiles=profiles)

    final = result["waveform"]
    assert np.max(np.abs(final)) <= 1.0


def test_generate_segment_missing_clone_file():
    """generate_segment raises RuntimeError (wrapped) for missing clone reference."""
    engine = PodcastEngine()
    profile = {"type": "clone", "value": "non_existent_voice.wav"}

    with pytest.raises(RuntimeError, match="Cloning reference audio not found"):
        engine.generate_segment("Test", profile=profile)


def test_generate_segment_unknown_type():
    """generate_segment raises RuntimeError (wrapped) for unknown speaker type."""
    engine = PodcastEngine()
    profile = {"type": "magic", "value": "whatever"}

    with pytest.raises(RuntimeError, match="Unknown speaker type"):
        engine.generate_segment("Test", profile=profile)


def test_multi_segment_podcast(monkeypatch):
    """Multiple segments concatenate correctly with padding."""
    engine = PodcastEngine()
    dummy_wav = np.ones(1000, dtype=np.float32) * 0.5
    monkeypatch.setattr(engine, "generate_segment", lambda text, profile, **kwargs: (dummy_wav, 24000))

    script = [
        {"role": "Host", "text": "Welcome"},
        {"role": "Guest", "text": "Thanks"},
        {"role": "Host", "text": "Bye"},
    ]
    profiles = {
        "Host": {"type": "preset", "value": "Ryan"},
        "Guest": {"type": "preset", "value": "Serena"}
    }
    result = engine.generate_podcast(script, profiles=profiles)

    assert result is not None
    # Still produces audio even with failures
    assert len(result["waveform"]) > 3000


def test_segment_error_is_skipped(monkeypatch):
    """If one segment fails, the rest still generate."""
    engine = PodcastEngine()
    call_count = [0]

    def mock_segment(text, profile, **kwargs):
        call_count[0] += 1
        if call_count[0] == 2:
            raise RuntimeError("Simulated failure")
        return (np.zeros(1000, dtype=np.float32), 24000)

    monkeypatch.setattr(engine, "generate_segment", mock_segment)

    script = [
        {"role": "A", "text": "One"},
        {"role": "B", "text": "Two"},  # This will fail
        {"role": "C", "text": "Three"},
    ]
    profiles = {"A": {}, "B": {}, "C": {}}
    result = engine.generate_podcast(script, profiles=profiles)

    assert result is not None
    # Still produces audio even with failures
    assert len(result["waveform"]) > 2000
