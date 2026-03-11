import sys
import transformers

def test_print_info():
    print(f"\nPython Version: {sys.version}")
    print(f"Transformers Version: {transformers.__version__}")
    print(f"Transformers File: {transformers.__file__}")
    print("SYS PATH:")
    for p in sys.path:
        print(f"  {p}")
    
    from transformers.models.auto import AutoFeatureExtractor
    print("AutoFeatureExtractor imported successfully")
