import unittest
import numpy as np
import sys
from pathlib import Path

# Add post_processor_modules to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tests.analytic_test_case import AnalyticTestCase
except ImportError:
    from analytic_test_case import AnalyticTestCase
from processing.primary_field_amplitude_subtractor import PrimaryFieldAmplitudeSubtractor

class TestAmplitudeSubtraction(AnalyticTestCase):
    
    def test_offset_removal(self):
        """
        Verify that the amplitude subtractor correctly removes DC offsets
        calculated from the border.
        """
        # 1. Define known offsets
        # [Ux_I, Ux_Q, Uy_I, Uy_Q, Uz_I, Uz_Q]
        known_offsets = np.array([1.5, -0.5, 2.0, 0.0, -1.0, 0.5])
        
        # 2. Add offsets to base signal
        input_data = self.generator.add_dc_offset(self.base_data, known_offsets)
        
        # 3. Run subtraction
        subtractor = PrimaryFieldAmplitudeSubtractor(border_width=2)
        subtracted_data, recovered_offsets = subtractor.subtract_primary_field(input_data)
        
        # 4. Verify recovered offsets
        # Since the base signal (sin*cos) averages to ~0 on the border for a sufficiently
        # large integer number of cycles, the mean of (Signal + Offset) should be approx Offset.
        # My generator uses 'kx' such that it's half a cycle.
        # Wait, sin(kx * x) limits -range/2 to +range/2.
        # If kx = 2*pi / (2*range), then argument goes from -pi/2 to +pi/2.
        # sin(-pi/2) = -1, sin(pi/2) = 1.
        # Average of sin(x) on [-pi/2, pi/2] is 0.
        # So the mean of the base signal on the border should be reasonably close to 0,
        # provided the sampling is symmetric.
        
        print("\nAmplitude Subtraction Test Results:")
        print(f"  Expected Offsets: {known_offsets}")
        print(f"  Recovered Offsets: {recovered_offsets}")
        
        self.assertArrayAlmostEqual(recovered_offsets, known_offsets, tolerance=0.1, 
                                  msg="Recovered offsets diverge from injected DC offsets")
        
        # 5. Verify residual mean on border is 0
        border_pixels = subtractor.extract_border_pixels(subtracted_data)
        residual_mean = np.mean(border_pixels, axis=0)
        
        print(f"  Residual Mean on border: {residual_mean}")
        self.assertArrayAlmostEqual(residual_mean, np.zeros(6), tolerance=1e-6, 
                                  msg="Mean amplitude not zeroed on border")

if __name__ == '__main__':
    unittest.main()
