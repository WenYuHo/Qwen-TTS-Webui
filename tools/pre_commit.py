import os
import sys
from pathlib import Path
import re

def check_no_print():
    """Fail if print() is used in src/backend (except specific allowed files)."""
    print("🔍 Checking for forbidden print() statements...")
    src_dir = Path("src/backend")
    errors = []
    
    for py_file in src_dir.rglob("*.py"):
        if "test" in py_file.name: continue
        
        content = py_file.read_text(encoding="utf-8")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if re.search(r"^\s*print\(", line) or re.search(r"[^.]print\(", line):
                # Allow if comment on same line says # allow-print
                if "# allow-print" not in line:
                    errors.append(f"{py_file}:{i+1} - forbidden print() found")

    if errors:
        print("❌ FAILED: Found print() statements. Use logging.")
        for e in errors:
            print(f"   {e}")
        return False
    print("✅ No print() statements found.")
    return True

def check_tests_exist():
    """Ensure every new .py file in src/backend has a test."""
    print("🔍 Checking test coverage existence...")
    # Get list of added/modified python files
    # This is a heuristic; in a real hook we'd check git diff --cached
    return True # Placeholder for now to avoid blocking legacy code

def main():
    print("🛑 PRE-COMMIT ENFORCEMENT")
    print("-" * 30)
    
    checks = [
        check_no_print(),
        # Add more checks here
    ]
    
    if all(checks):
        print("-" * 30)
        print("✅ ALL CHECKS PASSED. Ready to commit.")
        sys.exit(0)
    else:
        print("-" * 30)
        print("❌ CHECKS FAILED. Fix issues before committing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
