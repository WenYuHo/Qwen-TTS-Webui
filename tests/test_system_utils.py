import os
import time
import json
import numpy as np
import pytest
from pathlib import Path
from src.backend.utils import AudioPostProcessor, AuditManager, StorageManager

def test_audio_post_processor_eq():
    # Create dummy waveform
    sr = 24000
    wav = np.random.uniform(-1, 1, sr).astype(np.float32)
    
    # Test flat (no change)
    out_flat = AudioPostProcessor.apply_eq(wav, sr, preset="flat")
    assert np.array_equal(wav, out_flat)
    
    # Test broadcast (should change waveform)
    out_bc = AudioPostProcessor.apply_eq(wav, sr, preset="broadcast")
    assert not np.array_equal(wav, out_bc)
    assert len(out_bc) == len(wav)

def test_audio_post_processor_reverb():
    sr = 24000
    wav = np.random.uniform(-1, 1, sr).astype(np.float32)
    
    # Test zero intensity (no change)
    out_none = AudioPostProcessor.apply_reverb(wav, sr, intensity=0.0)
    assert np.array_equal(wav, out_none)
    
    # Test positive intensity (should be different)
    out_rev = AudioPostProcessor.apply_reverb(wav, sr, intensity=0.5)
    assert not np.array_equal(wav, out_rev)
    assert len(out_rev) == len(wav)

def test_audit_manager(tmp_path):
    # Mock AuditManager with temp directory
    am = AuditManager()
    am.file_path = tmp_path / "audit.json"
    
    # Test logging
    am.log_event("test_event", {"data": 123}, "completed")
    log = am.get_log()
    assert len(log) == 1
    assert log[0]["type"] == "test_event"
    assert log[0]["metadata"]["data"] == 123
    
    # Test sanitization (remove sensitive data)
    am.log_event("large_event", {"wav": [1,2,3], "other": "ok"}, "failed")
    log = am.get_log()
    assert "wav" not in log[1]["metadata"]
    assert log[1]["metadata"]["other"] == "ok"

def test_storage_manager(tmp_path):
    # Setup temp directories
    uploads = tmp_path / "uploads"
    videos = tmp_path / "videos"
    uploads.mkdir()
    videos.mkdir()
    
    sm = StorageManager(max_age_days=7)
    sm.targets = [uploads, videos]
    
    # Create a fresh file
    f_new = uploads / "new.txt"
    f_new.write_text("fresh")
    
    # Create an old file (simulated by setting mtime back)
    f_old = videos / "old.mp4"
    f_old.write_text("stale")
    old_time = time.time() - (10 * 86400) # 10 days ago
    os.utime(f_old, (old_time, old_time))
    
    # Run prune
    sm.prune()
    
    assert f_new.exists()
    assert not f_old.exists()
