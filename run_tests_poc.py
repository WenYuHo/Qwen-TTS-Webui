import subprocess
import os
import sys

def run_tests():
    print("Running tests with coverage...")
    try:
        # Run pytest with coverage for src directory
        # Using a subset of tests for efficiency first
        result = subprocess.run(
            ["pytest", "--cov=src", "--cov-report=term-missing", "tests/smoke_test.py"],
            capture_output=True,
            text=True
        )
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        
        # Also try to run all tests if smoke tests pass
        if result.returncode == 0:
            print("\nSmoke tests passed. Running all tests for full coverage baseline...")
            # This might take a while, so we might want to cap it
            # But for a baseline, let's try
            result_full = subprocess.run(
                ["pytest", "--cov=src", "--cov-report=term-missing"],
                capture_output=True,
                text=True,
                timeout=300 # 5 minute timeout
            )
            print("FULL STDOUT:")
            print(result_full.stdout)
            print("FULL STDERR:")
            print(result_full.stderr)
            
            with open("tests/coverage_baseline.md", "w") as f:
                f.write("# TESTING COVERAGE BASELINE\n\n")
                f.write("## OVERALL SUMMARY\n\n")
                f.write("```\n")
                f.write(result_full.stdout)
                f.write("\n```\n")
                f.write("\n## RELIABILITY GAPS\n\n")
                f.write("- [ ] Identify modules with < 80% coverage\n")
                f.write("- [ ] Review missed lines in core logic\n")
                
            print("\nCoverage baseline report created at tests/coverage_baseline.md")
        else:
            print("Smoke tests failed. Fixing baseline script.")
            
    except Exception as e:
        print(f"Error running tests: {e}")

if __name__ == "__main__":
    run_tests()
