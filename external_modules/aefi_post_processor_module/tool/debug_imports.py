import sys
from pathlib import Path

# tool/ est dans le module : external_modules/ doit être sur sys.path pour importer aefi_post_processor_module.
MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR.parent))
import traceback
import os

print("="*40)
print("DEBUGGING IMPORTS")
print("="*40)
print(f"Current Working Directory: {os.getcwd()}")
print(f"Script Path: {Path(__file__).resolve()}")

expected_path = str(MODULE_DIR.parent)
print(f"On sys.path: {expected_path}")
print(f"sys.path[0]: {sys.path[0]}")

print("\n--- TEST 1: Import processing ---")
try:
    import aefi_post_processor_module.processing as processing
    print("✅ import processing success")
    print(f"processing file: {processing.__file__}")
except:
    print("❌ import processing failed")
    traceback.print_exc()

print("\n--- TEST 2: Import tests package ---")
try:
    import aefi_post_processor_module.domain.processing._tests as tests
    print("✅ import tests success")
    print(f"tests file: {tests.__file__}")
except:
    print("❌ import tests failed")
    traceback.print_exc()

print("\n--- TEST 3: Import specific test module ---")
try:
    from aefi_post_processor_module.domain.processing._tests import analytic_test_case
    print("✅ from tests import analytic_test_case success")
except:
    print("❌ from tests import analytic_test_case failed")
    traceback.print_exc()

print("\n--- TEST 4: Import synthetic_scan_generator inside analytic_test_case ---")
try:
    from aefi_post_processor_module.domain.processing._tests import synthetic_scan_generator
    print("✅ from tests import synthetic_scan_generator success")
except:
    print("❌ from tests import synthetic_scan_generator failed")
    traceback.print_exc()
