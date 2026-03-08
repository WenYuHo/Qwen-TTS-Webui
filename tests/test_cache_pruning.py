import pytest
import numpy as np
from src.backend.utils import prune_dict_cache, _eq_filter_cache, AudioPostProcessor

def test_prune_dict_cache():
    """Verify that prune_dict_cache removes oldest items correctly."""
    cache = {i: i for i in range(10)}

    # 1. Prune with limit 5, count 3
    prune_dict_cache(cache, limit=5, count=3)

    # Since 10 > 5, it should remove 3 oldest (0, 1, 2)
    assert len(cache) == 7
    assert 0 not in cache
    assert 1 not in cache
    assert 2 not in cache
    assert 3 in cache

    # 2. Prune with limit 10, count 5 (no change expected since len=7)
    prune_dict_cache(cache, limit=10, count=5)
    assert len(cache) == 7

    # 3. Prune with count larger than len
    prune_dict_cache(cache, limit=1, count=20)
    assert len(cache) == 0

def test_eq_filter_cache_pruning():
    """Verify that EQ filter cache triggers pruning."""
    # Mock scipy_signal for AudioPostProcessor.apply_eq
    import src.backend.utils as utils
    from unittest.mock import MagicMock

    original_scipy = utils.scipy_signal
    utils.scipy_signal = MagicMock()
    utils.scipy_signal.butter.return_value = (np.array([1.0], dtype=np.float32), np.array([1.0], dtype=np.float32))
    utils.scipy_signal.lfilter.return_value = np.array([1.0, 2.0, 3.0], dtype=np.float32)

    _eq_filter_cache.clear()

    # Fill cache up to limit (200)
    for i in range(200):
        _eq_filter_cache[(f"preset_{i}", 24000)] = (None, None)

    assert len(_eq_filter_cache) == 200

    # Adding one more should trigger pruning (limit 200, count 20)
    # So it should go 200 -> 180 -> 181
    AudioPostProcessor.apply_eq(np.array([0.0, 0.0], dtype=np.float32), 24000, "broadcast")

    assert len(_eq_filter_cache) == 181

    # Cleanup
    utils.scipy_signal = original_scipy
