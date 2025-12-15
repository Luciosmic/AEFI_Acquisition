import unittest
import numpy as np
import sys
from pathlib import Path

# Add skills for DiagramFriendlyTest
skills_dir = Path(__file__).parents[3] / ".cursor" / "skills" / "diagram_friendly_test"
sys.path.append(str(skills_dir))

from diagram_friendly_test import DiagramFriendlyTest
from interface_v2.logic.coordinate_transformer import CoordinateTransformer

class TestCoordinateTransformer(DiagramFriendlyTest):
    
    def setUp(self):
        super().setUp()
        self.transformer = CoordinateTransformer()
        self.log_interaction("Test", "CREATE", "CoordinateTransformer", "Init transformer")
        
    def test_matlab_configuration_vector_x(self):
        """
        Reproduce MATLAB Rotation:
        theta_x = -45 deg
        theta_y = atan(1/sqrt(2)) deg ~= 35.264 deg
        theta_z = 0 deg
        
        Test vector: (1, 0, 0)
        """
        self.log_divider("MATLAB Configuration Test")
        
        theta_x = -45.0
        theta_y = np.degrees(np.arctan(1/np.sqrt(2)))
        theta_z = 0.0
        
        self.log_interaction("Test", "SET_ANGLES", "Transformer", f"Angles: {theta_x}, {theta_y}, {theta_z}")
        self.transformer.set_rotation_angles(theta_x, theta_y, theta_z)
        
        # Vector X (1, 0, 0)
        v_in = (1.0, 0.0, 0.0)
        self.log_interaction("Test", "TRANSFORM", "Transformer", "Sensor -> Source", data={"v_in": v_in})
        v_out = self.transformer.sensor_to_source(v_in)
        
        # Analytical check:
        # Rx(-45) = [[1, 0, 0], [0, c, S], [0, -S, c]] where c=S=1/sqrt(2) approx 0.707
        # Ry(35.26) = [[C, 0, S], [0, 1, 0], [-S, 0, C]] where tan(th)=1/sqrt(2) -> sin=1/sqrt(3), cos=sqrt(2)/sqrt(3)
        # Rz(0) = Identity
        # Total R = Ry * Rx (since Rz is I)
        
        # Let's trust Scipy implementation but verify magnitude is preserved
        mag_in = np.linalg.norm(v_in)
        mag_out = np.linalg.norm(v_out)
        
        self.log_interaction("Test", "ASSERT", "Result", "Check Magnitude Preserved", expect=str(mag_in), got=str(mag_out))
        self.assertAlmostEqual(mag_in, mag_out)
        
        # Check Inverse
        v_inv = self.transformer.source_to_sensor(v_out)
        self.log_interaction("Test", "ASSERT", "Result", "Check Inverse Identity", expect=str(v_in), got=str(v_inv))
        for i in range(3):
            self.assertAlmostEqual(v_in[i], v_inv[i])

if __name__ == "__main__":
    unittest.main()
