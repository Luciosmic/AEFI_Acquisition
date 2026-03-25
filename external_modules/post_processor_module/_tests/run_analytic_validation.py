"""
Analytic Validation Runner
Executes all analytic analytic validation tests and generates a summary report.
"""

import unittest
import sys
import os
from pathlib import Path

# Add 'tools/post_processor_modules' to path
# This allows 'import processing' and 'import tests'
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_tests():
    """Discover and run all tests in the tests directory."""
    
    # 1. Discover tests
    test_loader = unittest.TestLoader()
    test_dir = Path(__file__).parent
    suite = test_loader.discover(start_dir=str(test_dir), pattern='test_*.py')
    
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
