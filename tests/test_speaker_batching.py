import pytest
import numpy as np
import torch
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

@pytest.fixture
def mock_model():
    # Mocking parts of the model that we don't need for the test
    with patch("transformers.AutoConfig.register"),          patch("transformers.AutoModel.register"),          patch("transformers.AutoProcessor.register"):
        from backend.qwen_tts.core.models.modeling_qwen3_tts import Qwen3TTSForConditionalGeneration

        # Create a mock instance instead of calling __init__
        model = MagicMock(spec=Qwen3TTSForConditionalGeneration)
        model.device = torch.device("cpu")
        model.dtype = torch.float32
        model.speaker_encoder_sample_rate = 24000

        # Mock speaker_encoder
        model.speaker_encoder = MagicMock()
        model.speaker_encoder.side_effect = lambda x: torch.randn(x.shape[0], 128)

        # Re-attach the actual method we want to test
        model.extract_speaker_embedding = Qwen3TTSForConditionalGeneration.extract_speaker_embedding.__get__(model, Qwen3TTSForConditionalGeneration)

        return model

def test_extract_speaker_embedding_single(mock_model):
    sr = 24000
    audio = np.random.randn(sr).astype(np.float32)

    emb = mock_model.extract_speaker_embedding(audio, sr)

    assert isinstance(emb, torch.Tensor)
    assert emb.shape == (128,)
    assert mock_model.speaker_encoder.called

def test_extract_speaker_embedding_batch(mock_model):
    sr = 24000
    audios = [
        np.random.randn(sr).astype(np.float32),
        np.random.randn(sr // 2).astype(np.float32),
        np.random.randn(sr * 2).astype(np.float32)
    ]

    embs = mock_model.extract_speaker_embedding(audios, sr)

    assert isinstance(embs, torch.Tensor)
    assert embs.shape == (3, 128)
    assert mock_model.speaker_encoder.called

    # Verify mel_spectrogram was called with padded input
    # The batch of 3 should result in (3, T, 128) mels after transpose
    args, kwargs = mock_model.speaker_encoder.call_args
    mels_input = args[0]
    assert mels_input.shape[0] == 3
    assert mels_input.shape[1] >= 180

if __name__ == "__main__":
    pytest.main([__file__])
