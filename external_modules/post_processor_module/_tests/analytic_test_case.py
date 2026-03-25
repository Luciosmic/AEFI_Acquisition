"""
AnalyticTestCase - Base class for analytic tests.
"""

import unittest
import numpy as np
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tests.synthetic_scan_generator import SyntheticScanGenerator
except ImportError:
    from synthetic_scan_generator import SyntheticScanGenerator

class AnalyticTestCase(unittest.TestCase):
    """Base class for analytic tests."""
    
    def setUp(self):
        """Setup test environment."""
        self.generator = SyntheticScanGenerator(grid_size=50, scan_range=10.0)
        self.base_data = self.generator.generate_base_signal()
        
    def assertArrayAlmostEqual(self, actual, expected, tolerance=1e-6, msg=""):
        """Verify arrays match within tolerance."""
        diff = np.abs(actual - expected)
        max_diff = np.max(diff)
        if max_diff > tolerance:
            self.fail(f"{msg} Max difference {max_diff} > tolerance {tolerance}")
            
    def assertScalarAlmostEqual(self, actual, expected, tolerance=1e-6, msg=""):
        """Verify scalars match within tolerance."""
        diff = abs(actual - expected)
        if diff > tolerance:
            self.fail(f"{msg} Difference {diff} > tolerance {tolerance}")
