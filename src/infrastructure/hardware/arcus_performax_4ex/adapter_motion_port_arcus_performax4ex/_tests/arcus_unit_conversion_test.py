import unittest
from unittest.mock import MagicMock
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from infrastructure.hardware.arcus_performax_4ex.adapter_motion_port_arcus_performax4ex.adapter_motion_port_arcus_performax4ex import ArcusAdapter
from infrastructure.hardware.arcus_performax_4ex.driver_arcus_performax4ex import ArcusPerformax4EXController
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


class TestArcusUnitConversion(unittest.TestCase):
    def setUp(self):
        self.adapter = ArcusAdapter()
        self.adapter.set_microns_per_pulse(21.8)  # bench transmission (1/16 microstepping)
        self.mock_controller = MagicMock(spec=ArcusPerformax4EXController)
        self.adapter.set_controller(self.mock_controller)

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

    def test_the_exported_increments_are_the_ones_the_move_command_sends(self):
        """The export and the move share one conversion: they cannot drift apart."""
        self.adapter.set_microns_per_pulse(20.62)

        self.adapter._internal_move_to(Position2D(x=135.0, y=12.34))

        sent = {call.args[0]: call.args[1] for call in self.mock_controller.move_to.call_args_list}
        self.assertEqual((sent["X"], sent["Y"]), self.adapter.mm_to_increments(135.0, 12.34))

    def test_reported_increments_are_read_from_the_controller(self):
        self.mock_controller.get_position.side_effect = lambda axis: 1234.0 if axis == "X" else 567.0

        self.assertEqual(self.adapter.read_increments(), (1234, 567))

    def test_axis_limits_follow_the_measured_travel_in_increments(self):
        from domain.test_bench_configuration.physical_bench_limits.physical_bench_limits import (
            X_TRAVEL_INCREMENTS,
            Y_TRAVEL_INCREMENTS,
        )

        max_x, max_y = self.adapter.get_axis_limits()

        self.assertAlmostEqual(max_x, X_TRAVEL_INCREMENTS * 21.8 / 1000.0)
        self.assertAlmostEqual(max_y, Y_TRAVEL_INCREMENTS * 21.8 / 1000.0)

    def test_the_middle_of_the_bench_stays_the_same_increment_when_the_factor_changes(self):
        """Correcting µm/increment rescales mm, never the physical middle of the rails."""
        from domain.test_bench_configuration.physical_bench_limits.physical_bench_limits import X_TRAVEL_INCREMENTS

        middles_in_increments = []
        for microns_per_pulse in (20.62, 21.46, 21.8):
            self.adapter.set_microns_per_pulse(microns_per_pulse)
            middle_mm = self.adapter.get_axis_limits()[0] / 2.0
            middles_in_increments.append(middle_mm * self.adapter.STEPS_PER_MM)

        for middle in middles_in_increments:
            self.assertAlmostEqual(middle, X_TRAVEL_INCREMENTS / 2.0, places=6)


if __name__ == '__main__':
    unittest.main()
