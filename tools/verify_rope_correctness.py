
import torch
import numpy as np
from src.backend.qwen_tts.core.models.modeling_qwen3_tts import Qwen3TTSTalkerRotaryEmbedding, Qwen3TTSRotaryEmbedding
from src.backend.qwen_tts.core.models.configuration_qwen3_tts import Qwen3TTSTalkerConfig, Qwen3TTSTalkerCodePredictorConfig

def verify_correctness():
    # Mock original implementation for comparison
    def original_talker_forward(self, x, position_ids):
        inv_freq_expanded = self.inv_freq[None, None, :, None].float().expand(3, position_ids.shape[1], -1, 1)
        position_ids_expanded = position_ids[:, :, None, :].float()
        freqs = (inv_freq_expanded.float() @ position_ids_expanded.float()).transpose(2, 3)
        emb = torch.cat((freqs, freqs), dim=-1)
        cos = emb.cos() * self.attention_scaling
        sin = emb.sin() * self.attention_scaling
        return cos, sin

    def original_base_forward(self, x, position_ids):
        inv_freq_expanded = self.inv_freq[None, :, None].float().expand(position_ids.shape[0], -1, 1).to(x.device)
        position_ids_expanded = position_ids[:, None, :].float()
        freqs = (inv_freq_expanded.float() @ position_ids_expanded.float()).transpose(1, 2)
        emb = torch.cat((freqs, freqs), dim=-1)
        cos = emb.cos() * self.attention_scaling
        sin = emb.sin() * self.attention_scaling
        return cos, sin

    talker_config = Qwen3TTSTalkerConfig(
        hidden_size=1024,
        num_attention_heads=16,
        rope_scaling={"rope_type": "linear", "factor": 1.0, "mrope_section": [16, 16, 16], "interleaved": False}
    )
    predictor_config = Qwen3TTSTalkerCodePredictorConfig(
        hidden_size=1024,
        num_attention_heads=16,
    )

    talker_rope = Qwen3TTSTalkerRotaryEmbedding(talker_config)
    base_rope = Qwen3TTSRotaryEmbedding(predictor_config)

    # Test Talker
    x = torch.randn(3, 2, 10, 64)
    pos = torch.arange(10).view(1, 1, -1).expand(3, 2, -1)

    new_cos, new_sin = talker_rope(x, pos)
    old_cos, old_sin = original_talker_forward(talker_rope, x, pos)

    assert torch.allclose(new_cos, old_cos, atol=1e-6), "Talker cos mismatch"
    assert torch.allclose(new_sin, old_sin, atol=1e-6), "Talker sin mismatch"
    print("Talker correctness verified!")

    # Test Base
    x_base = torch.randn(2, 10, 64)
    pos_base = torch.arange(10).view(1, -1).expand(2, -1)

    new_cos_b, new_sin_b = base_rope(x_base, pos_base)
    old_cos_b, old_sin_b = original_base_forward(base_rope, x_base, pos_base)

    assert torch.allclose(new_cos_b, old_cos_b, atol=1e-6), "Base cos mismatch"
    assert torch.allclose(new_sin_b, old_sin_b, atol=1e-6), "Base sin mismatch"
    print("Base correctness verified!")

if __name__ == "__main__":
    verify_correctness()
