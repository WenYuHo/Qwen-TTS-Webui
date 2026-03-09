import pytest
import numpy as np
import os
from unittest.mock import MagicMock, patch
from backend.podcast_engine import PodcastEngine
from backend.engine_modules.synthesizer import VoiceSynthesizer

@pytest.fixture
def engine(tmp_path):
    # Use real objects where possible, but mock the heavy ones
    with patch('backend.podcast_engine.get_model'), \
         patch('backend.podcast_engine.PodcastEngine.precompute_virtual_presets'):
        
        # Setup real DiskCache/HybridCache with tmp_path
        os.environ["QWEN_ENABLE_INT8"] = "false"
        eng = PodcastEngine()
        # Manually override the caches to use local dicts for simplicity in this test
        eng.prompt_cache = {}
        eng.preset_embeddings = {}
        eng.clone_embedding_cache = {}
        eng.transcription_cache = {}
        eng.translation_cache = {}
        
        # Re-init synthesizer with these dicts
        eng.synthesizer.prompt_cache = eng.prompt_cache
        eng.synthesizer.preset_embeddings = eng.preset_embeddings
        eng.synthesizer.clone_embedding_cache = eng.clone_embedding_cache
        eng.synthesizer.transcription_cache = eng.transcription_cache
        eng.synthesizer.translation_cache = eng.translation_cache
        
        return eng

def test_synthesizer_uses_precomputed_style(engine):
    # Setup
    mock_prompt = [MagicMock()]
    engine.prompt_cache["design:A calm male voice"] = mock_prompt
    
    mock_base_model = MagicMock()
    mock_base_model.generate_voice_clone.return_value = ([np.zeros(1000)], 24000)
    
    # We patch get_model in synthesizer.py
    with patch('backend.engine_modules.synthesizer.get_model', return_value=mock_base_model):
        profile = {"type": "design", "value": "A calm male voice"}
        
        # Act
        wav, sr = engine.generate_segment("Hello", profile)
        
        # Assert
        assert mock_base_model.generate_voice_clone.called
        assert not mock_base_model.generate_voice_design.called

def test_synthesizer_falls_back_if_not_precomputed(engine):
    # Setup
    engine.prompt_cache = {} 
    engine.synthesizer.prompt_cache = {}
    
    mock_design_model = MagicMock()
    mock_design_model.generate_voice_design.return_value = ([np.zeros(1000)], 24000)
    
    with patch('backend.engine_modules.synthesizer.get_model', return_value=mock_design_model):
        profile = {"type": "design", "value": "Unknown style"}
        
        # Act
        wav, sr = engine.generate_segment("Hello", profile)
        
        # Assert
        assert mock_design_model.generate_voice_design.called
