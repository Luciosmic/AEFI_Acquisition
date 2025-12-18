import unittest
from unittest.mock import MagicMock
import sys
from pathlib import Path

from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from domain.shared.value_objects.position_2d import Position2D

# Ensure src is in path
src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

class TestArcusUnitConversion(unittest.TestCase):
    def setUp(self):
        self.adapter = ArcusAdapter()
        # Mock the controller/stage
        self.mock_stage = MagicMock()
        self.adapter._stage = self.mock_stage
        
        # Constants from implementation
        self.MICRONS_PER_STEP = 43.6
        self.MM_PER_STEP = 0.0436
        self.STEPS_PER_MM = 1.0 / 0.0436
        self.STEPS_PER_CM = 1.0 / 0.00436

    def test_move_to_conversion(self):
        # Arrange
        target_pos = Position2D(x=10.0, y=20.0) # mm
        expected_steps_x = int(10.0 * self.STEPS_PER_MM)
        expected_steps_y = int(20.0 * self.STEPS_PER_MM)
        
        # Act
        self.adapter.move_to(target_pos)
        
        # Assert
        self.mock_stage.move_to.assert_any_call("X", expected_steps_x)
        self.mock_stage.move_to.assert_any_call("Y", expected_steps_y)

    def test_get_current_position_conversion(self):
        # Arrange
        # Simulate reading steps from hardware
        steps_x = 1000
        steps_y = 2000
        self.mock_stage.get_position.side_effect = lambda axis: steps_x if axis == "X" else steps_y
        
        expected_mm_x = steps_x * self.MM_PER_STEP
        expected_mm_y = steps_y * self.MM_PER_STEP
        
        # Act
        pos = self.adapter.get_current_position()
        
        # Assert
        self.assertAlmostEqual(pos.x, expected_mm_x, places=5)
        self.assertAlmostEqual(pos.y, expected_mm_y, places=5)

    def test_set_speed_conversion(self):
        # Arrange
        speed_cm_s = 1.0 # cm/s
        expected_hz = int(speed_cm_s * self.STEPS_PER_CM)
        
        # Act
        self.adapter.set_speed(speed_cm_s)
        
        # Assert
        self.mock_stage.query.assert_any_call(f"HSX={expected_hz}")
        self.mock_stage.query.assert_any_call(f"HSY={expected_hz}")

if __name__ == '__main__':
    unittest.main()
