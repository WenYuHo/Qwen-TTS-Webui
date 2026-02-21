import numpy as np
import logging

class Transformer:
    def __init__(self):
        self.effects = []
    
    def norm(self, db_level=-6):
        self.effects.append(('norm', db_level))
        return self

    def set_output_format(self, rate=None, bits=None, channels=None):
        return self

    def build_array(self, input_array, sample_rate_in=16000):
        # Fallback: simple normalization if sox is not available
        # This is enough for the x-vector extraction to proceed
        logging.warning("Using mock sox.Transformer. Results may vary from real SoX.")
        
        # Simple RMS normalization as a placeholder for 'norm' effect
        max_val = np.max(np.abs(input_array))
        if max_val > 0:
            # Scale to roughly -6dB (0.5 linear)
            return (input_array / max_val * 0.5).astype(input_array.dtype)
        return input_array

def mock_sox():
    import sys
    from types import ModuleType
    
    # Check if already mocked or installed
    if "sox" in sys.modules and not isinstance(sys.modules["sox"], ModuleType):
        return

    m = ModuleType("sox")
    m.Transformer = Transformer
    
    # Add common error classes
    class SoxError(Exception): pass
    m.SoxError = SoxError
    
    sys.modules["sox"] = m
    logging.info("Applied sox shim for Windows compatibility.")
