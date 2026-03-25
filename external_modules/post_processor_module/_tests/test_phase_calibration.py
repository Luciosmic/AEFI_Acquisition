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
from processing.primary_field_phase_calibrator import PrimaryFieldPhaseCalibrator

class TestPhaseCalibration(AnalyticTestCase):
    
    def test_phase_recovery(self):
        """
        Verify that the phase calibrator recovers the correct phase offset
        and successfully zeroes out the Quadrature component on the border.
        """
        # 1. Define known phase offsets (radians)
        # Using different angles for X, Y, Z to ensure independence
        known_phases = (np.deg2rad(10.0), np.deg2rad(-25.0), np.deg2rad(45.0))
        
        # 2. Add phase offset to base signal (which has Q=0 originally)
        # Note: add_phase_offset rotates (I, Q) by phi. 
        # So new vector is V * exp(j * phi)
        input_data = self.generator.add_phase_offset(self.base_data, known_phases)
        
        # 3. Run calibration
        calibrator = PrimaryFieldPhaseCalibrator(border_width=2)
        calibrated_data, recovered_phases = calibrator.calibrate(input_data)
        
        # 4. Verify recovered phases
        # The calibrator finds the angle of the vector mean on the border: theta
        # And rotates by -theta. 
        # Since our signal is S * exp(j * phi), the angle should be phi.
        # So we expect recovered_phases['x'] approx known_phases[0]
        
        print("\nPhase Calibration Test Results:")
        axes = ['x', 'y', 'z']
        for i, axis in enumerate(axes):
            expected = known_phases[i]
            # Convert recovered (radians) back for comparison
            actual = recovered_phases[axis]
            
            print(f"  Axis {axis}: Expected {np.rad2deg(expected):.2f}°, Got {np.rad2deg(actual):.2f}°")
            
            # Tolerance note: Since the field isn't constant, the mean angle on the border
            # might slightly differ from the global phase offset if the base signal 
            # has its own "structural" phase variation.
            # However, my base signal (sin*cos) is Real-only, so its phase is 0 or 180 (pi).
            # If the border averages to 0 (cancellation of positive and negative parts),
            # then finding the phase might be unstable (atan2(0,0)).
            # Checks: My base signal is sin(kx*x)*cos(ky*y).
            # On the border, values are not all zero.
            # But the MEAN of the vector sum could be zero if symmetric.
            # Ideally, we should add a DC component or a carrier so the vector sum is non-zero.
            # Or use a base signal that is predominantly one-signed on the border?
            # Wait, the calibrator uses `mean(phases)`. 
            # `phases = arctan2(q, i)`. `mean_phase = mean(phases)`.
            # If signal oscillates +1 and -1, phases will be 0 and pi. Mean is pi/2.
            # That's dangerous.
            # Correct approach for phase calibrator usually assumes a "Carrier" or "Primary Field"
            # which is strong and constant-ish.
            # Let's modify the test signal to simulated a Primary Field (Constant).
            
            # RE-RUN logic with a constant DC field + small variation
            
        # Re-doing data generation for valid test
        # Base signal: Constant field (Primary field) + Perturbation
        # V = [1.0, 0] + [small_var, 0]
        
        dc_field = np.ones_like(self.base_data) * 1.0 # Amplitude 1.0
        # Zero out the Q components for DC field (strictly Real)
        dc_field[:, :, [1, 3, 5]] = 0.0
        
        # Perturbed signal
        base_signal = dc_field + 0.1 * self.base_data 
        
        # Apply phase offset
        input_data_dc = self.generator.add_phase_offset(base_signal, known_phases)
        
        # Run calibration again
        calibrated_data, recovered_phases = calibrator.calibrate(input_data_dc)
        
        for i, axis in enumerate(axes):
            expected = known_phases[i]
            actual = recovered_phases[axis]
            self.assertScalarAlmostEqual(actual, expected, tolerance=1e-3, 
                                       msg=f"Phase mismatch on axis {axis}")

        # 5. Verify Q component minimization on border
        border_pixels = calibrator.extract_border_pixels(calibrated_data)
        
        # Check mean Q on border is close to 0
        # Indices for Q are 1, 3, 5
        q_indices = [1, 3, 5]
        mean_q = np.mean(border_pixels[:, q_indices], axis=0)
        
        print(f"  Residual Mean Q on border: {mean_q}")
        self.assertArrayAlmostEqual(mean_q, np.zeros(3), tolerance=1e-6, 
                                  msg="Quadrature component not zeroed on border")

if __name__ == '__main__':
    unittest.main()
