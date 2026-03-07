
import torch
import time
import numpy as np
from src.backend.qwen_tts.core.models.modeling_qwen3_tts import Qwen3TTSTalkerRotaryEmbedding, Qwen3TTSRotaryEmbedding
from src.backend.qwen_tts.core.models.configuration_qwen3_tts import Qwen3TTSTalkerConfig, Qwen3TTSConfig

def benchmark_rope(model_class, config, device='cpu', batch_sizes=[1, 8, 16], seq_lengths=[1, 128, 512], iterations=100):
    print(f"\nBenchmarking {model_class.__name__} on {device}")
    rope = model_class(config).to(device)

    # Warmup
    dummy_x = torch.randn(1, 1, 1, 64, device=device)
    dummy_pos = torch.zeros(3, 1, 1, device=device).long() if model_class == Qwen3TTSTalkerRotaryEmbedding else torch.zeros(1, 1, device=device).long()
    for _ in range(10):
        rope(dummy_x, dummy_pos)

    for bs in batch_sizes:
        for seq_len in seq_lengths:
            if model_class == Qwen3TTSTalkerRotaryEmbedding:
                x = torch.randn(3, bs, seq_len, 64, device=device)
                pos = torch.arange(seq_len, device=device).view(1, 1, -1).expand(3, bs, -1)
            else:
                x = torch.randn(bs, seq_len, 64, device=device)
                pos = torch.arange(seq_len, device=device).view(1, -1).expand(bs, -1)

            start = time.perf_counter()
            for _ in range(iterations):
                cos, sin = rope(x, pos)
            end = time.perf_counter()

            avg_ms = (end - start) * 1000 / iterations
            print(f"BS: {bs:2d}, Seq: {seq_len:4d} | Avg: {avg_ms:8.4f} ms")

if __name__ == "__main__":
    talker_config = Qwen3TTSTalkerConfig(
        hidden_size=1024,
        num_attention_heads=16,
        rope_scaling={"rope_type": "linear", "factor": 1.0, "mrope_section": [16, 16, 16], "interleaved": False}
    )

    base_config = Qwen3TTSConfig(
        talker_config={
            "hidden_size": 1024,
            "num_attention_heads": 16,
        }
    )
    # Actually Qwen3TTSRotaryEmbedding uses Qwen3TTSConfig which has its own hidden_size etc if not using talker_config?
    # Wait, Qwen3TTSRotaryEmbedding constructor:
    # def __init__(self, config: Qwen3TTSConfig, device=None):
    #   ...
    #   self.max_seq_len_cached = config.max_position_embeddings

    # Qwen3TTSConfig doesn't have max_position_embeddings directly, it seems it might be missing from my read or I missed something.
    # Ah, Qwen3TTSConfig inherits from PretrainedConfig.
    # Let me re-read Qwen3TTSConfig in configuration_qwen3_tts.py.
    # It has talker_config.

    # Actually, let's look at Qwen3TTSRotaryEmbedding again.
    # It uses config.max_position_embeddings.
    # In configuration_qwen3_tts.py, Qwen3TTSConfig doesn't define it.
    # But Qwen3TTSTalkerCodePredictorConfig does.

    # Wait, Qwen3TTSTalkerRotaryEmbedding uses Qwen3TTSTalkerConfig.
    # Qwen3TTSRotaryEmbedding uses Qwen3TTSConfig.

    # Let me check Qwen3TTSRotaryEmbedding's usage in modeling_qwen3_tts.py.
    # It's used in Qwen3TTSTalkerCodePredictorModel:
    # self.rotary_emb = Qwen3TTSRotaryEmbedding(config=config)
    # where config is Qwen3TTSTalkerCodePredictorConfig.

    from src.backend.qwen_tts.core.models.configuration_qwen3_tts import Qwen3TTSTalkerCodePredictorConfig
    predictor_config = Qwen3TTSTalkerCodePredictorConfig(
        hidden_size=1024,
        num_attention_heads=16,
    )

    benchmark_rope(Qwen3TTSTalkerRotaryEmbedding, talker_config)
    benchmark_rope(Qwen3TTSRotaryEmbedding, predictor_config)

    if torch.cuda.is_available():
        benchmark_rope(Qwen3TTSTalkerRotaryEmbedding, talker_config, device='cuda')
        benchmark_rope(Qwen3TTSRotaryEmbedding, predictor_config, device='cuda')
