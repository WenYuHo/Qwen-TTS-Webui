import os
import sys
import time
import soundfile as sf
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("src"))

# Mock server state if needed, or import engine directly
from backend.podcast_engine import PodcastEngine

def test_long_form_stability():
    print("--- Starting LONG-FORM Stability Test ---")
    
    # A text long enough to trigger the chunking logic (>150 chars per sentence or multiple sentences)
    long_text = (
        "This is a test of the long-form stability system. "
        "We need to ensure that the voice remains consistent over time, "
        "even when the input text is quite lengthy and complex. "
        "Traditionally, attention mechanisms might drift after a few seconds, "
        "causing the voice to sound garbled or hallucinate strange sounds. "
        "By splitting this into smaller, manageable chunks, we hope to maintain high fidelity "
        "from the very first word to the very last period."
    )
    
    profile = {"type": "preset", "value": "Ryan"}
    
    try:
        engine = PodcastEngine()
        print(f"Synthesizing {len(long_text)} characters...")
        
        start_time = time.time()
        # Use stream_synthesize to test the generator
        generator = engine.stream_synthesize(long_text, profile)
        
        all_wavs = []
        sr = 24000
        
        for i, (wav, sample_rate) in enumerate(generator):
            print(f"  Received chunk {i+1} (Size: {len(wav)} samples)")
            all_wavs.append(wav)
            sr = sample_rate
            
        if not all_wavs:
            raise RuntimeError("No audio chunks received!")
            
        import numpy as np
        final_wav = np.concatenate(all_wavs)
        end_time = time.time()
        
        output_path = "test_long_form.wav"
        sf.write(output_path, final_wav, sr)
        
        duration = len(final_wav) / sr
        print(f"✅ Long-form synthesis successful.")
        print(f"   Time: {end_time - start_time:.2f}s")
        print(f"   Audio Duration: {duration:.2f}s")
        print(f"   Saved to {output_path}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_long_form_stability()
