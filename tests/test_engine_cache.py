import pytest
import shutil
from pathlib import Path
import torch
import numpy as np
from backend.utils.cache import DiskCache, HybridCache

def test_disk_cache_persistence(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_name = "test_cache"
    
    # 1. Write to cache
    cache = DiskCache(cache_dir, cache_name)
    test_key = "my_key"
    test_value = {"data": [1, 2, 3], "tensor": torch.zeros(5)}
    cache.set(test_key, test_value)
    
    # 2. Re-initialize and read
    new_cache = DiskCache(cache_dir, cache_name)
    loaded_value = new_cache.get(test_key)
    
    assert loaded_value is not None
    assert loaded_value["data"] == [1, 2, 3]
    assert torch.equal(loaded_value["tensor"], torch.zeros(5))

def test_hybrid_cache_sync(tmp_path):
    cache_dir = tmp_path / "cache"
    disk = DiskCache(cache_dir, "hybrid")
    hybrid = HybridCache(disk)
    
    # 1. Set in hybrid (goes to memory and disk)
    hybrid["foo"] = "bar"
    assert "foo" in hybrid
    
    # 2. Check disk directly
    assert disk.get("foo") == "bar"
    
    # 3. New hybrid instance should find it
    disk2 = DiskCache(cache_dir, "hybrid")
    hybrid2 = HybridCache(disk2)
    assert hybrid2["foo"] == "bar"
    assert "foo" in hybrid2
