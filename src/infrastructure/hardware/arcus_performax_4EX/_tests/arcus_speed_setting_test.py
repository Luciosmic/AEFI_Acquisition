import unittest
from unittest.mock import MagicMock
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import ArcusPerformax4EXController


class TestArcusSpeedSetting(unittest.TestCase):
    def setUp(self):
        self.adapter = ArcusAdapter()
        self.mock_controller = MagicMock(spec=ArcusPerformax4EXController)
        self.adapter.set_controller(self.mock_controller)

        # Read from adapter so the test stays consistent with whatever
        # arcus_default_config.json sets as microns_per_step.
        self.STEPS_PER_MM = self.adapter.STEPS_PER_MM

    def test_speed_conversion_6_54_cm_s(self):
        # Arrange
        target_speed_mm_s = 65.4  # 6.54 cm/s = 65.4 mm/s

        # Expected Hz: int(65.4 * 22.9357...) = int(1499.99...) = 1499
        expected_hz = int(target_speed_mm_s * self.STEPS_PER_MM)

        # Act
        self.adapter.set_speed(target_speed_mm_s)

        # Assert
        self.mock_controller.set_speed.assert_called_once_with(expected_hz)

    def test_set_speed_mode_fast_applies_hs_and_acc(self):
        self.adapter.set_speed_mode("fast")

        self.mock_controller.set_speed.assert_called_once_with(3000)
        self.mock_controller.set_acceleration.assert_called_once_with(500)

    def test_set_speed_mode_slow_and_medium_share_acc(self):
        self.adapter.set_speed_mode("slow")
        self.mock_controller.set_speed.assert_called_once_with(800)
        self.mock_controller.set_acceleration.assert_called_once_with(300)

        self.mock_controller.reset_mock()

        self.adapter.set_speed_mode("medium")
        self.mock_controller.set_speed.assert_called_once_with(1500)
        self.mock_controller.set_acceleration.assert_called_once_with(300)

    def test_set_speed_mode_unknown_raises(self):
        with self.assertRaises(ValueError):
            self.adapter.set_speed_mode("ludicrous")


if __name__ == '__main__':
    unittest.main()
