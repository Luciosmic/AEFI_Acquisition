import queue
import time
import unittest

from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.hardware.arcus_performax_4EX.fake.fake_arcus_performax4ex_controller import (
    FakeArcusPerformax4EXController,
    _MEASURED_TIMING_BY_HS,
)
from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.mocks.adapter_mock_i_motion_port import measured_move_duration_s


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
        self.assertTrue(self.controller.is_moving("x"))  # non-blocking, like pylablib

        self.controller.wait_move("x")
        self.assertEqual(self.controller.get_position("x"), 250.0)
        self.assertFalse(self.controller.is_moving("x"))

    def test_move_duration_follows_the_bench_measurement(self):
        self.controller.connect()
        self.controller.home_both()
        self.controller.set_speed(1500)  # medium preset
        t0, speed_steps_s = _MEASURED_TIMING_BY_HS[1500]

        start = time.perf_counter()
        self.controller.move_to("x", 300)
        self.controller.move_to("y", 150)  # both axes together: cost = longest axis
        while self.controller.is_moving():
            time.sleep(0.005)
        self.assertAlmostEqual(time.perf_counter() - start, t0 + 300 / speed_steps_s, delta=0.03)
        self.assertEqual(self.controller.get_position("y"), 150)

    def test_stop_freezes_the_axis_mid_move(self):
        self.controller.connect()
        self.controller.home_both()
        self.controller.move_to("x", 10_000)
        time.sleep(0.5)
        self.controller.stop("x")
        stopped_at = self.controller.get_position("x")
        self.assertFalse(self.controller.is_moving("x"))
        self.assertTrue(0 < stopped_at < 10_000)
        time.sleep(0.1)
        self.assertEqual(self.controller.get_position("x"), stopped_at)

    def test_real_adapter_over_fake_matches_measured_port_timing(self):
        """Acceptance: fake controller + REAL ArcusAdapter reproduce the bench
        port-level duration (move_to -> MotionCompleted). Tolerance covers the
        USB query latency the fake doesn't simulate (~0.1-0.2 s on the bench)."""
        bus = InMemoryEventBus()
        completed = queue.Queue()
        bus.subscribe("motioncompleted", completed.put)
        self.controller.connect()
        self.controller.home_both()
        adapter = ArcusAdapter(event_bus=bus)
        adapter.set_microns_per_pulse(21.8)  # transmission of the measurement
        adapter.set_controller(self.controller)
        adapter.enable()
        try:
            adapter.set_speed_mode("medium")
            position = Position2D(600.0, 600.0)
            self.controller.set_position_reference("x", round(position.x * adapter.STEPS_PER_MM))
            self.controller.set_position_reference("y", round(position.y * adapter.STEPS_PER_MM))
            for d in (10.0, 50.0):  # diagonal: also checks the axes move together
                target = Position2D(position.x + d, position.y + d)
                start = time.perf_counter()
                adapter.move_to(target)
                completed.get(timeout=10.0)
                expected = measured_move_duration_s(position, target, "medium")
                self.assertAlmostEqual(time.perf_counter() - start, expected, delta=0.25)
                position = target
        finally:
            adapter.disable()

    def test_real_adapter_refuses_to_move_without_a_transmission(self):
        """No mm/pulse factor from the domain: no guessed default, no move."""
        self.controller.connect()
        self.controller.home_both()
        adapter = ArcusAdapter()
        adapter.set_controller(self.controller)
        with self.assertRaises(RuntimeError):
            adapter.move_to(Position2D(10.0, 10.0))
        self.assertFalse(self.controller.is_moving())

    def test_set_axis_params_roundtrip(self):
        self.controller.connect()
        result = self.controller.set_axis_params("x", hs=3000)
        self.assertEqual(result["hs"], 3000)
        self.assertEqual(self.controller.get_axis_params_dict("x")["hs"], 3000)

    def test_real_arcus_adapter_runs_unmodified_against_the_fake(self):
        """The whole point: real ArcusAdapter worker/monitor code, fake controller."""
        self.controller.connect()
        adapter = ArcusAdapter()
        adapter.set_microns_per_pulse(21.8)
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
