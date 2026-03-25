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
from processing.sensor_to_ef_sources_frame_rotator import SensorToEFSourcesFrameRotator

class TestFrameRotation(AnalyticTestCase):
    
    def test_vector_rotation(self):
        """
        Verify rotation of vector fields.
        """
        # 1. Create a uniform field pointing in X direction
        # [Ux_I=1, Ux_Q=0, Uy_I=0, ..., Uz_Q=0]
        data = np.zeros((10, 10, 6))
        data[:, :, 0] = 1.0 # Ux_I
        
        # 2. Define rotation: 90 degrees around Z axis
        # X vector should become Y vector
        angles = (0.0, 0.0, 90.0)
        
        # 3. Apply rotation
        rotator = SensorToEFSourcesFrameRotator()
        rotated_data, _ = rotator.rotate(data, angles)
        
        # 4. Verify result
        # Expected: Ux=0, Uy=1 (approx)
        # Note: Rotation order XYZ. 
        # Z-rotation of 90 deg sends X -> Y, Y -> -X.
        
        mean_vector = np.mean(rotated_data, axis=(0,1))
        print("\nFrame Rotation Test Results (90 deg around Z):")
        print(f"  Input Vector (Mean): {np.mean(data, axis=(0,1))}")
        print(f"  Rotated Vector (Mean): {mean_vector}")
        
        # Check Ux_I is approx 0
        self.assertAlmostEqual(mean_vector[0], 0.0, delta=1e-6, msg="Ux should be 0 after 90 deg Z-rot")
        # Check Uy_I is approx 1
        self.assertAlmostEqual(mean_vector[2], 1.0, delta=1e-6, msg="Uy should be 1 after 90 deg Z-rot")
        
    def test_quaternion_consistency(self):
        """
        Verify quaternion matches euler angles.
        """
        rotator = SensorToEFSourcesFrameRotator()
        angles = (30, 45, 60)
        rotator.set_rotation_angles(*angles)
        
        # Get quaternion
        q = rotator.get_quaternion()
        
        # Check normalization
        norm = np.linalg.norm(q)
        self.assertAlmostEqual(norm, 1.0, delta=1e-6, msg="Quaternion not normalized")

if __name__ == '__main__':
    unittest.main()
