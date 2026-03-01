import pytest
import numpy as np
from pydub import AudioSegment
from backend.podcast_engine import PodcastEngine
from pathlib import Path
import os
import shutil
import io
import soundfile as sf
from unittest.mock import MagicMock, patch

@pytest.fixture
def engine():
    # Mock engine that doesn't load real models
    class MockEngine(PodcastEngine):
        def __init__(self):
            self.upload_dir = Path("uploads")
            self.upload_dir.mkdir(exist_ok=True)
            self.bgm_dir = Path("bgm")
            self.bgm_dir.mkdir(exist_ok=True)
            self.shared_assets_dir = Path("shared_assets")
            self.shared_assets_dir.mkdir(exist_ok=True)
            self.bgm_cache = {}
            self.mix_embedding_cache = {}

        def generate_segment(self, text, profile=None, language="auto", model=None):
            # Return 1s of 0.1 amplitude (some dialogue)
            sr = 24000
            wav = 0.1 * np.ones(sr)
            return wav, sr

        def _get_model_type_for_profile(self, profile):
            return "Base"

        def _resolve_paths(self, path):
             return [Path(path)]

    return MockEngine()

def test_ducking_mixing(engine):
    with patch("backend.podcast_engine.get_model", return_value=MagicMock()):
        # 1. Create a dummy BGM file in shared_assets (WAV)
        bgm_path = Path("shared_assets/test_mood.wav")
        sr = 24000
        t = np.linspace(0, 10, 10*sr)
        bgm_wav = 0.5 * np.ones(len(t))
        sf.write(bgm_path, bgm_wav, sr)

        script = [{"role": "Speaker1", "text": "Hello", "pause_after": 1.0}]
        profiles = {"Speaker1": {"type": "preset", "value": "ryan"}}

        # 2. Generate NO BGM
        res_no_bgm = engine.generate_podcast(script, profiles, bgm_mood=None, ducking_level=0.0)
        e_diag = np.sum(np.abs(res_no_bgm["waveform"][:24000]))

        # 3. Generate BGM NO DUCK
        res_no = engine.generate_podcast(script, profiles, bgm_mood="test_mood.wav", ducking_level=0.0)
        e_no = np.sum(np.abs(res_no["waveform"][:24000]))

        # 4. Generate BGM DUCK
        res_duck = engine.generate_podcast(script, profiles, bgm_mood="test_mood.wav", ducking_level=1.0)
        e_duck = np.sum(np.abs(res_duck["waveform"][:24000]))

        assert e_no > e_diag # BGM added energy
        assert e_duck < e_no # Ducking reduced energy

        if bgm_path.exists(): bgm_path.unlink()
