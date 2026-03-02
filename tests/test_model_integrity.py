import os
import pytest
from pathlib import Path
from src.backend.config import LTX_MODELS_PATH, find_ltx_model, find_model_path, MODELS

def test_ltx_checkpoint_integrity():
    """Verify that LTX checkpoints exist and are valid (not just zero-byte files)."""
    # Smallest model check
    ltxv_path = find_ltx_model("ltxv_checkpoint")
    if ltxv_path:
        assert ltxv_path.exists()
        assert ltxv_path.stat().st_size > 1000000000 # > 1GB
        
        # Optional: Attempt header read if safetensors is installed
        try:
            from safetensors import safe_open
            with safe_open(str(ltxv_path), framework="pt") as f:
                assert len(f.keys()) > 0
        except ImportError:
            pass

def test_qwen_checkpoint_integrity():
    """Verify that Qwen model directories contain expected files."""
    for key, repo_id in MODELS.items():
        path = find_model_path(repo_id)
        if path:
            assert path.is_dir()
            # Check for standard transformer files
            config = path / "config.json"
            assert config.exists()
            
            # Check for weights (either .bin or .safetensors)
            weights = list(path.glob("*.safetensors")) + list(path.glob("*.bin"))
            assert len(weights) > 0

def test_gemma_dir_integrity():
    """Verify LTX-2 dependency (Gemma) if present."""
    gemma_path = find_ltx_model("gemma_dir")
    if gemma_path:
        assert gemma_path.is_dir()
        assert (gemma_path / "config.json").exists()
        assert len(list(gemma_path.glob("*.safetensors"))) > 0
