import unittest

from infrastructure.hardware.arcus_performax_4EX.fake.fake_arcus_performax4ex_controller import (
    FakeArcusPerformax4EXController,
)
from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter


class TestFakeArcusPerformax4EXController(unittest.TestCase):
    def setUp(self):
        self.controller = FakeArcusPerformax4EXController()

    def test_move_before_connect_raises(self):
        with self.assertRaises(RuntimeError):
            self.controller.get_position("x")

    def test_move_before_homing_raises(self):
        self.controller.connect()
        with self.assertRaises(RuntimeError):
            self.controller.move_to("x", 100.0)

    def test_home_both_then_move_updates_position(self):
        self.controller.connect()
        self.controller.home_both(blocking=True)

        self.assertTrue(self.controller.is_homed("x"))
        self.assertTrue(self.controller.is_homed("y"))
        self.assertEqual(self.controller.get_position("x"), 0.0)

        self.controller.move_to("x", 250.0)

        self.assertEqual(self.controller.get_position("x"), 250.0)
        self.assertFalse(self.controller.is_moving("x"))

    def test_set_axis_params_roundtrip(self):
        self.controller.connect()
        result = self.controller.set_axis_params("x", hs=3000)
        self.assertEqual(result["hs"], 3000)
        self.assertEqual(self.controller.get_axis_params_dict("x")["hs"], 3000)

    def test_real_arcus_adapter_runs_unmodified_against_the_fake(self):
        """The whole point: real ArcusAdapter worker/monitor code, fake controller."""
        self.controller.connect()
        adapter = ArcusAdapter()
        adapter.set_controller(self.controller)
        adapter.enable()
        try:
            adapter.home()
            adapter.wait_until_stopped(timeout=5.0)
            pos = adapter.get_current_position()
            self.assertEqual(pos.x, 0.0)
            self.assertEqual(pos.y, 0.0)
        finally:
            adapter.disable()


if __name__ == "__main__":
    unittest.main()
