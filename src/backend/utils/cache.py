import os
import json
import pickle
import hashlib
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("studio")

class DiskCache:
    """A simple persistent disk cache for engine artifacts."""
    def __init__(self, cache_dir: Path, name: str):
        self.cache_dir = cache_dir / name
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.name = name
        logger.info(f"Initialized disk cache '{name}' at {self.cache_dir}")

    def _get_path(self, key: str) -> Path:
        # Use MD5 to avoid filesystem issues with complex keys
        hashed_key = hashlib.md5(key.encode('utf-8')).hexdigest()
        return self.cache_dir / hashed_key

    def get(self, key: str) -> Optional[Any]:
        path = self._get_path(key)
        if not path.exists():
            return None
        
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to read from cache '{self.name}': {e}")
            return None

    def set(self, key: str, value: Any):
        path = self._get_path(key)
        try:
            with open(path, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            logger.warning(f"Failed to write to cache '{self.name}': {e}")

    def clear(self):
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)

class HybridCache(dict):
    """A dictionary-like object that syncs with a DiskCache."""
    def __init__(self, disk_cache: DiskCache, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disk_cache = disk_cache

    def __getitem__(self, key):
        if super().__contains__(key):
            return super().__getitem__(key)
        
        val = self.disk_cache.get(key)
        if val is not None:
            # Sync to memory
            super().__setitem__(key, val)
            return val
        raise KeyError(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.disk_cache.set(key, value)

    def __contains__(self, key):
        if super().__contains__(key):
            return True
        return self.disk_cache.get(key) is not None
