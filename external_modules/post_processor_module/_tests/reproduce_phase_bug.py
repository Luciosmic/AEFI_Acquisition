
import unittest
import numpy as np
from tools.post_processor_modules.processing.primary_field_phase_calibrator import PrimaryFieldPhaseCalibrator

class TestPhaseCalibrationBug(unittest.TestCase):
    
    def test_nan_reference_no_correction(self):
        """
        Test that using a NaN reference results in NO calibration (theta=0),
        leaving other pixels uncorrected (leaking Q).
        """
        calibrator = PrimaryFieldPhaseCalibrator()
        
        # Create 3x3 grid, 1 channel
        # Pixel (0,0) is NaN
        # Pixel (1,1) has I=1, Q=1 (Phase 45 deg)
        data = np.full((3, 3, 2), np.nan)
        
        # Channel 0 (X): I at index 0, Q at index 1
        # Set (1, 1) to valid data
        data[1, 1, 0] = 1.0 # I
        data[1, 1, 1] = 1.0 # Q
        
        # Try calibrating with (0,0) - NaN
        # The calibrator should now search for a valid point (like 1,1) and use it.
        calibrated_nan, meta_nan = calibrator.calibrate(data, reference_idx=(0, 0), axis_pairs=[(0, 1)])
        
        # Expectation: theta should be ~45deg (from 1,1) because it found the neighbor.
        # So Q at (1,1) should be 0.0
        q_result = calibrated_nan[1, 1, 1]
        print(f"NaN Ref -> Q Result: {q_result} (Expected ~0.0 due to auto-search)")
        
        self.assertAlmostEqual(q_result, 0.0)
        self.assertNotEqual(meta_nan['axis_0'], 0.0) # Theta should NOT be 0
        self.assertEqual(meta_nan['reference_used'], (1, 1)) # Should have found (1,1)
        
    def test_valid_reference_corrects(self):
        """
        Control test: Using (1,1) as reference should zero Q.
        """
        calibrator = PrimaryFieldPhaseCalibrator()
        data = np.full((3, 3, 2), np.nan)
        data[1, 1, 0] = 1.0
        data[1, 1, 1] = 1.0
        
        # Calibrate with valid ref
        calibrated, meta = calibrator.calibrate(data, reference_idx=(1, 1), axis_pairs=[(0, 1)])
        
        q_result = calibrated[1, 1, 1]
        print(f"Valid Ref -> Q Result: {q_result} (Expected ~0.0)")
        
        self.assertAlmostEqual(q_result, 0.0)

if __name__ == '__main__':
    unittest.main()
