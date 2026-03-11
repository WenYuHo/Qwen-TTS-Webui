import pytest
import numpy as np
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from backend.podcast_engine import PodcastEngine

@pytest.fixture(autouse=True)
def mock_model_loader():
    with patch("backend.model_loader._ensure_qwen_tts"),          patch("backend.model_loader.get_model") as mock_get:
        mock_model = MagicMock()
        mock_model.generate_custom_voice.return_value = ([np.zeros(24000)], 24000)
        mock_model.generate_voice_design.return_value = ([np.zeros(24000)], 24000)
        mock_model.generate_voice_clone.return_value = ([np.zeros(24000)], 24000)
        mock_model.create_voice_clone_prompt.return_value = [MagicMock()]
        mock_get.return_value = mock_model

        # Mock load_model directly to avoid FileNotFoundError
        with patch("backend.model_loader.manager.load_model") as mock_load:
            mock_load.return_value = mock_model
            yield mock_model

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

    # Ensure watermark is enabled for this test by patching the global variable in the module
    from backend.api.system import SystemSettings
    monkeypatch.setattr("backend.podcast_engine._system_settings", SystemSettings(watermark_audio=True))

    script = [{"role": "ryan", "text": "Hello"}]
    profiles = {"ryan": {"type": "preset", "value": "Ryan"}}
    result = engine.generate_podcast(script, profiles=profiles)

    assert result is not None
    assert "waveform" in result
    assert result["sample_rate"] == 24000
    # 1s (dummy) + 2s (padding) + 0.1s (watermark) = 3.1s = 74400 samples
    assert len(result["waveform"]) == 74400

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

def test_generate_segment_missing_clone_file(monkeypatch):
    """generate_segment raises RuntimeError (wrapped) for missing clone reference."""
    engine = PodcastEngine()
    def mock_resolve(path):
        raise FileNotFoundError("Missing")
    monkeypatch.setattr(engine.synthesizer, "_resolve_paths", mock_resolve)

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

def test_generate_segment_with_ref_text(monkeypatch):
    """Test ICL mode activation when ref_text is provided."""
    engine = PodcastEngine()
    
    # Mock dependencies
    mock_model = MagicMock()
    mock_model.create_voice_clone_prompt.return_value = [MagicMock()]
    mock_model.generate_voice_clone.return_value = ([np.zeros(24000)], 24000)
    
    # Mock internal methods to avoid I/O
    monkeypatch.setattr(engine.synthesizer, "_resolve_paths", lambda x: [Path("dummy.wav")])
    monkeypatch.setattr(engine.synthesizer, "_extract_audio_with_cache", lambda x: "dummy.wav")
    monkeypatch.setattr(engine.synthesizer.__class__, "_validate_ref_audio", lambda *args: None)
    
    # Mock soundfile to avoid file I/O for silence padding
    with patch("soundfile.read", return_value=(np.zeros(24000), 24000)), \
         patch("soundfile.write"):
        
        profile = {"type": "clone", "value": "dummy.wav", "ref_text": "Reference transcript"}
        
        engine.generate_segment("Test", profile, model=mock_model)
        
        mock_model.create_voice_clone_prompt.assert_called_once()
        call_kwargs = mock_model.create_voice_clone_prompt.call_args.kwargs
        assert call_kwargs.get("ref_text") == "Reference transcript"
        assert call_kwargs.get("x_vector_only_mode") is False

def test_generate_segment_without_ref_text(monkeypatch):
    """Test standard cloning when ref_text is missing."""
    engine = PodcastEngine()
    
    mock_model = MagicMock()
    mock_model.create_voice_clone_prompt.return_value = [MagicMock()]
    mock_model.generate_voice_clone.return_value = ([np.zeros(24000)], 24000)
    
    monkeypatch.setattr(engine.synthesizer, "_resolve_paths", lambda x: [Path("dummy.wav")])
    monkeypatch.setattr(engine.synthesizer, "_extract_audio_with_cache", lambda x: "dummy.wav")
    monkeypatch.setattr(engine.synthesizer.__class__, "_validate_ref_audio", lambda *args: None)
    
    profile = {"type": "clone", "value": "dummy.wav"}
    
    engine.generate_segment("Test", profile, model=mock_model)
    
    mock_model.create_voice_clone_prompt.assert_called_once()
    call_kwargs = mock_model.create_voice_clone_prompt.call_args.kwargs
    assert call_kwargs.get("ref_text") is None
    assert call_kwargs.get("x_vector_only_mode") is True

def test_stream_voice_changer(monkeypatch):
    """Test the streaming S2S logic with segments and windowing."""
    import torch
    engine = PodcastEngine()
    
    # 1. Mock transcribe_audio to return segments
    mock_segments = [
        {"text": "Hello", "start": 0.5, "end": 1.5},
        {"text": "World", "start": 2.0, "end": 2.5}
    ]
    monkeypatch.setattr(engine, "transcribe_audio", lambda x: {"segments": mock_segments, "text": "Hello World"})
    
    # 2. Mock model calls
    mock_model = MagicMock()
    mock_model.generate_voice_clone.return_value = ([np.zeros(1000)], 24000)
    mock_model.create_voice_clone_prompt.return_value = [MagicMock()]
    
    # 3. Mock internal methods
    monkeypatch.setattr("backend.podcast_engine.get_model", lambda x: mock_model)
    monkeypatch.setattr(engine, "_resolve_paths", lambda x: [Path("dummy.wav")])
    monkeypatch.setattr(engine, "get_speaker_embedding", lambda x, **kwargs: torch.zeros(128))
    monkeypatch.setattr("backend.podcast_engine.VideoEngine.is_video", lambda x: False)
    
    # Mock soundfile.read to return a 5s dummy waveform (24k * 5 = 120000)
    # We patch it where it's used (backend.podcast_engine.sf)
    with patch("backend.podcast_engine.sf.read", return_value=(np.zeros(120000), 24000)):
        chunks = list(engine.stream_voice_changer("dummy.wav", preserve_prosody=True))
        
        assert len(chunks) == 2
        # Verify model was called twice
        assert mock_model.generate_voice_clone.call_count == 2
        
        # Verify windowing logic (3s window for short segments)
        last_call_args = mock_model.create_voice_clone_prompt.call_args_list[0]
        ref_audio_arg = last_call_args.kwargs.get("ref_audio")
        assert isinstance(ref_audio_arg, tuple)
        # 3s window @ 24k = 72000 samples
        assert len(ref_audio_arg[0]) == 72000
