import unittest
from unittest.mock import MagicMock, patch
import time
import threading
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.hardware.arcus_performax_4EX.driver_arcus_performax4EX import ArcusPerformax4EXController
from domain.value_objects.geometric.position_2d import Position2D

class TestArcusAsyncArchitecture(unittest.TestCase):
    def setUp(self):
        self.mock_controller = MagicMock(spec=ArcusPerformax4EXController)
        self.mock_controller.is_connected.return_value = True
        self.mock_controller.is_moving.return_value = False
        self.mock_controller.get_position.return_value = 0.0

        self.adapter = ArcusAdapter()
        self.adapter.set_controller(self.mock_controller)
        self.adapter.enable()

        # Read calibration from adapter so assertions are consistent
        # with whatever arcus_default_config.json sets.
        self._steps_per_mm = self.adapter.STEPS_PER_MM

    def tearDown(self):
        self.adapter.disable()

    def test_move_to_is_non_blocking(self):
        pos = Position2D(x=10.0, y=20.0)
        steps_x = int(10.0 * self._steps_per_mm)
        steps_y = int(20.0 * self._steps_per_mm)

        start_time = time.time()
        self.adapter.move_to(pos)
        end_time = time.time()

        self.assertLess(end_time - start_time, 0.1, "move_to should return immediately")

        time.sleep(0.2)
        time.sleep(0.2)
        self.mock_controller.move_to.assert_any_call("X", steps_x)
        self.mock_controller.move_to.assert_any_call("Y", steps_y)

    def test_sequential_execution(self):
        pos1 = Position2D(x=10.0, y=10.0)
        pos2 = Position2D(x=20.0, y=20.0)
        steps_10 = int(10.0 * self._steps_per_mm)
        steps_20 = int(20.0 * self._steps_per_mm)

        self.adapter.move_to(pos1)
        self.adapter.move_to(pos2)

        time.sleep(0.5)

        calls = self.mock_controller.move_to.call_args_list
        self.assertEqual(len(calls), 4)
        self.assertEqual(calls[0][0][1], steps_10)  # X1
        self.assertEqual(calls[1][0][1], steps_10)  # Y1
        self.assertEqual(calls[2][0][1], steps_20)  # X2
        self.assertEqual(calls[3][0][1], steps_20)  # Y2

    def test_stop_clears_queue(self):
        self.mock_controller.move_to.side_effect = lambda a, p: time.sleep(0.2)

        pos1 = Position2D(x=10.0, y=10.0)
        pos2 = Position2D(x=20.0, y=20.0)

        self.adapter.move_to(pos1)
        self.adapter.move_to(pos2)

        time.sleep(0.05)
        self.adapter.stop()

        time.sleep(0.5)

        self.assertTrue(self.adapter._command_queue.empty())

    def test_set_reference(self):
        """set_reference delegates to controller.set_position_reference."""
        self.adapter.set_reference("x", 10.0)

        time.sleep(0.2)

        self.mock_controller.set_position_reference.assert_called_with("x", 10.0)

    def test_home_sets_reference(self):
        """home command automatically sets reference to 0."""
        self.adapter.home("x")

        time.sleep(0.2)

        self.mock_controller.home.assert_called()
        self.mock_controller.set_position_reference.assert_called_with("x", 0.0)

    def test_home_both_sets_reference(self):
        """home(None) sets reference for both axes."""
        self.adapter.home(None)

        time.sleep(0.2)

        self.mock_controller.home_both.assert_called()
        from unittest.mock import call
        self.mock_controller.set_position_reference.assert_has_calls(
            [call("x", 0.0), call("y", 0.0)], any_order=True
        )

    def test_emergency_stop_priority(self):
        """emergency_stop clears queue and sends immediate stop to controller."""
        pos1 = Position2D(x=10.0, y=10.0)
        pos2 = Position2D(x=20.0, y=20.0)

        self.adapter.move_to(pos1)
        self.adapter.move_to(pos2)

        self.adapter.emergency_stop()

        self.assertTrue(self.adapter._command_queue.empty())

        from unittest.mock import call
        self.mock_controller.stop.assert_has_calls(
            [call("X", immediate=True), call("Y", immediate=True)], any_order=True
        )

if __name__ == '__main__':
    unittest.main()
