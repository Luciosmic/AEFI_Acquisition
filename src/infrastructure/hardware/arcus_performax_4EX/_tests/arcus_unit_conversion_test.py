import unittest
from unittest.mock import MagicMock
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import ArcusPerformax4EXController
from domain.value_objects.geometric.position_2d import Position2D


class TestArcusUnitConversion(unittest.TestCase):
    def setUp(self):
        self.adapter = ArcusAdapter()
        self.mock_controller = MagicMock(spec=ArcusPerformax4EXController)
        self.adapter.set_controller(self.mock_controller)

        # Read calibration constants from the adapter instance after __init__
        # so the test stays consistent even if the config file changes.
        self.MM_PER_STEP = self.adapter.MM_PER_STEP
        self.STEPS_PER_MM = self.adapter.STEPS_PER_MM

    def test_move_to_conversion(self):
        # Arrange
        target_pos = Position2D(x=10.0, y=20.0)  # mm
        expected_steps_x = int(10.0 * self.STEPS_PER_MM)
        expected_steps_y = int(20.0 * self.STEPS_PER_MM)

        # Act — call the internal synchronous method to avoid async worker timing
        self.adapter._internal_move_to(target_pos)

        # Assert
        self.mock_controller.move_to.assert_any_call("X", expected_steps_x)
        self.mock_controller.move_to.assert_any_call("Y", expected_steps_y)

    def test_get_current_position_conversion(self):
        # Arrange
        steps_x = 1000
        steps_y = 2000
        self.mock_controller.get_position.side_effect = (
            lambda axis: steps_x if axis == "X" else steps_y
        )

        expected_mm_x = steps_x * self.MM_PER_STEP
        expected_mm_y = steps_y * self.MM_PER_STEP

        # Act
        pos = self.adapter.get_current_position()

        # Assert
        self.assertAlmostEqual(pos.x, expected_mm_x, places=5)
        self.assertAlmostEqual(pos.y, expected_mm_y, places=5)

    def test_set_speed_conversion(self):
        # Arrange — speed in mm/s (10 mm/s = 1 cm/s)
        speed_mm_s = 10.0
        expected_hz = max(10, min(int(speed_mm_s * self.STEPS_PER_MM), 100000))

        # Act
        self.adapter.set_speed(speed_mm_s)

        # Assert
        self.mock_controller.set_speed.assert_called_once_with(expected_hz)


if __name__ == '__main__':
    unittest.main()
