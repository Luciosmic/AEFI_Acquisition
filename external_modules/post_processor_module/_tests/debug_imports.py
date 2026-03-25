import sys
from pathlib import Path
import traceback
import os

print("="*40)
print("DEBUGGING IMPORTS")
print("="*40)
print(f"Current Working Directory: {os.getcwd()}")
print(f"Script Path: {Path(__file__).resolve()}")

# Add path like runner
expected_path = str(Path(__file__).parent.parent.resolve())
sys.path.insert(0, expected_path)
print(f"Added to sys.path: {expected_path}")
print(f"sys.path[0]: {sys.path[0]}")

print("\n--- TEST 1: Import processing ---")
try:
    import processing
    print("✅ import processing success")
    print(f"processing file: {processing.__file__}")
except:
    print("❌ import processing failed")
    traceback.print_exc()

print("\n--- TEST 2: Import tests package ---")
try:
    import tests
    print("✅ import tests success")
    print(f"tests file: {tests.__file__}")
except:
    print("❌ import tests failed")
    traceback.print_exc()

print("\n--- TEST 3: Import specific test module ---")
try:
    from tests import analytic_test_case
    print("✅ from tests import analytic_test_case success")
except:
    print("❌ from tests import analytic_test_case failed")
    traceback.print_exc()

print("\n--- TEST 4: Import synthetic_scan_generator inside analytic_test_case ---")
try:
    from tests import synthetic_scan_generator
    print("✅ from tests import synthetic_scan_generator success")
except:
    print("❌ from tests import synthetic_scan_generator failed")
    traceback.print_exc()
