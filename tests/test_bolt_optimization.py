import pytest
import numpy as np
from pathlib import Path
from src.backend.podcast_engine import PodcastEngine, _watermark_tone_cache
from src.backend.api.system import _settings

def test_resolve_paths_optimization(tmp_path):
    """Verify that _resolve_paths correctly identifies safe and unsafe paths using the new optimization."""
    # Setup mock environment
    engine = PodcastEngine()

    # upload_dir is pre-resolved in __init__
    upload_dir = engine.upload_dir
    safe_file = upload_dir / "test.wav"
    safe_file.touch()

    # 1. Test relative path within upload_dir
    resolved = engine._resolve_paths("test.wav")
    assert len(resolved) == 1
    assert resolved[0] == safe_file.resolve()

    # 2. Test absolute path within upload_dir
    resolved = engine._resolve_paths(str(safe_file))
    assert len(resolved) == 1
    assert resolved[0] == safe_file.resolve()

    # 3. Test path traversal (unsafe)
    with pytest.raises(PermissionError):
        engine._resolve_paths("../secret.txt")

    # 4. Test multiple paths
    another_file = upload_dir / "another.wav"
    another_file.touch()
    resolved = engine._resolve_paths(f"test.wav|{str(another_file)}")
    assert len(resolved) == 2
    assert resolved[0] == safe_file.resolve()
    assert resolved[1] == another_file.resolve()

def test_watermark_tone_caching():
    """Verify that the watermark tone is cached and reused for the same sample rate."""
    engine = PodcastEngine()
    _settings.watermark_audio = True
    sr = 24000
    wav = np.zeros(sr, dtype=np.float32)

    # Clear cache for deterministic test
    _watermark_tone_cache.clear()

    # 1. First call - should generate and cache
    # ⚡ Bolt: Cache key is now (sample_rate, num_channels)
    watermarked1 = engine._apply_audio_watermark(wav, sr)
    cache_key = (sr, 1) # mono
    assert cache_key in _watermark_tone_cache
    tone1 = _watermark_tone_cache[cache_key]

    # 2. Second call - should reuse from cache
    watermarked2 = engine._apply_audio_watermark(wav, sr)
    tone2 = _watermark_tone_cache[cache_key]

    # Verify it's the same object (identity check)
    assert tone1 is tone2
    assert np.array_equal(watermarked1, watermarked2)

    # 3. Different sample rate - should generate new entry
    sr2 = 44100
    wav2 = np.zeros(sr2, dtype=np.float32)
    watermarked3 = engine._apply_audio_watermark(wav2, sr2)
    cache_key2 = (sr2, 1)
    assert cache_key2 in _watermark_tone_cache
    assert _watermark_tone_cache[cache_key2] is not tone1

def test_watermark_disabled():
    """Verify that watermarking can be disabled via settings."""
    engine = PodcastEngine()
    _settings.watermark_audio = False
    sr = 24000
    wav = np.zeros(sr, dtype=np.float32)

    watermarked = engine._apply_audio_watermark(wav, sr)
    # If disabled, it should return the original wav (same length)
    assert len(watermarked) == len(wav)
    assert np.array_equal(watermarked, wav)

    # Restore settings
    _settings.watermark_audio = True
