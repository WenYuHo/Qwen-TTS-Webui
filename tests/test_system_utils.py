import os
import time
import json
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for direct testing if needed
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = str(ROOT_DIR / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from backend.utils import AudioPostProcessor, AuditManager, StorageManager, Profiler, ResourceMonitor

def test_audio_post_processor_eq():
    # Create dummy waveform
    sr = 24000
    wav = np.random.uniform(-1, 1, sr).astype(np.float32)
    
    # Test flat (no change)
    out_flat = AudioPostProcessor.apply_eq(wav, sr, preset="flat")
    assert np.array_equal(wav, out_flat)
    
    # Test broadcast (should change waveform if scipy is present)
    try:
        import scipy
        out_bc = AudioPostProcessor.apply_eq(wav, sr, preset="broadcast")
        assert not np.array_equal(wav, out_bc)
    except ImportError:
        # Should return original if scipy is missing
        out_bc = AudioPostProcessor.apply_eq(wav, sr, preset="broadcast")
        assert np.array_equal(wav, out_bc)

def test_audio_post_processor_reverb():
    sr = 24000
    wav = np.random.uniform(-1, 1, sr).astype(np.float32)
    
    # Test zero intensity (no change)
    out_none = AudioPostProcessor.apply_reverb(wav, sr, intensity=0.0)
    assert np.array_equal(wav, out_none)
    
    # Test positive intensity (should be different)
    out_rev = AudioPostProcessor.apply_reverb(wav, sr, intensity=0.5)
    assert not np.array_equal(wav, out_rev)

def test_audit_manager(tmp_path):
    # Mock AuditManager with temp directory
    am = AuditManager()
    am.file_path = tmp_path / "audit.json"
    
    # Test logging
    am.log_event("test_event", {"data": 123}, "completed")
    log = am.get_log()
    assert len(log) == 1
    assert log[0]["type"] == "test_event"
    
    # Test record rotation (1000 events limit)
    for _ in range(1005):
        am.log_event("flood", {}, "ok")
    log = am.get_log()
    assert len(log) == 1000

def test_storage_manager(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    
    sm = StorageManager(max_age_days=7)
    sm.targets = [uploads]
    
    # Create old file
    f_old = uploads / "stale.wav"
    f_old.write_text("old")
    old_time = time.time() - (10 * 86400)
    os.utime(f_old, (old_time, old_time))
    
    sm.prune()
    assert not f_old.exists()
    assert sm.get_stats()["total_pruned"] == 1

def test_profiler_runs():
    """Verify that profiler doesn't crash and logs output."""
    with Profiler("Test Profiling"):
        # Dummy workload
        sum([i*i for i in range(1000)])

def test_resource_monitor_metrics():
    """Verify resource monitor returns expected structure."""
    with patch("psutil.cpu_percent", return_value=15.5):
        with patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 45.0
            stats = ResourceMonitor.get_stats()
            
            assert stats["cpu_percent"] == 15.5
            assert stats["ram_percent"] == 45.0
            assert "gpu" in stats
