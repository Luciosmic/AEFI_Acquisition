"""
Analytic Validation Runner
Executes all analytic analytic validation tests and generates a summary report.
"""

import sys
from pathlib import Path

# tool/ est dans le module : external_modules/ doit être sur sys.path pour importer aefi_post_processor_module.
MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR.parent))

import unittest
import os

def run_tests():
    """Discover and run all tests in the tests directory."""
    
    # 1. Discover tests
    test_loader = unittest.TestLoader()
    test_dir = MODULE_DIR / "_tests"
    suite = test_loader.discover(start_dir=str(test_dir), top_level_dir=str(MODULE_DIR.parent), pattern='*_test.py')
    
    # 2. Run tests
    print("="*60)
    print("RUNNING ANALYTIC VALIDATION SUITE")
    print("="*60)
    print(f"Test Directory: {test_dir}\n")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 3. Report
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        print(f"Total Tests: {result.testsRun}")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED")
        print(f"Total Tests: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        sys.exit(1)

if __name__ == '__main__':
    run_tests()
