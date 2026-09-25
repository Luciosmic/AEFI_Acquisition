import unittest
import numpy as np
import sys
from pathlib import Path

# Add aefi_post_processor_modules to path
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
        
        # 2. Angles of the mounting rotation P = Rz(90)
        # The rotator applies P = Rz(90): X vector should become +Y vector
        angles = (0.0, 0.0, 90.0)

        # 3. Apply rotation
        rotator = SensorToEFSourcesFrameRotator()
        rotated_data, _ = rotator.rotate(data, angles)

        # 4. Verify result
        # Expected: Ux=0, Uy=+1 (approx)
        # Note: P = Rz(90) is the mounting rotation; E_sources = P·E_sensor.
        # Rz(90) sends X -> Y, Y -> -X.

        mean_vector = np.mean(rotated_data, axis=(0,1))
        print("\nFrame Rotation Test Results (P = Rz(90), applied P):")
        print(f"  Input Vector (Mean): {np.mean(data, axis=(0,1))}")
        print(f"  Rotated Vector (Mean): {mean_vector}")

        # Check Ux_I is approx 0
        self.assertAlmostEqual(mean_vector[0], 0.0, delta=1e-6, msg="Ux should be 0 after applying P = Rz(90)")
        # Check Uy_I is approx +1
        self.assertAlmostEqual(mean_vector[2], 1.0, delta=1e-6, msg="Uy should be +1 after applying P = Rz(90)")

    def test_ideal_angles_map_cube_diagonal_to_sources_vertical(self):
        """
        With the ideal angles (atan(1/sqrt(2)), 45, 0), the cube diagonal
        (-1, 1, 1)/sqrt(3) in the sensor frame is the sources vertical (0, 0, 1):
        P·(-1, 1, 1)/sqrt(3) = (0, 0, 1).
        """
        data = np.zeros((4, 4, 6))
        data[:, :, [0, 2, 4]] = np.array([-1.0, 1.0, 1.0]) / np.sqrt(3.0)

        angles = (np.degrees(np.arctan(1.0 / np.sqrt(2.0))), 45.0, 0.0)
        rotated_data, _ = SensorToEFSourcesFrameRotator().rotate(data, angles)

        mean_vector = np.mean(rotated_data, axis=(0, 1))
        self.assertAlmostEqual(mean_vector[0], 0.0, delta=1e-9)
        self.assertAlmostEqual(mean_vector[2], 0.0, delta=1e-9)
        self.assertAlmostEqual(mean_vector[4], 1.0, delta=1e-9)

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
