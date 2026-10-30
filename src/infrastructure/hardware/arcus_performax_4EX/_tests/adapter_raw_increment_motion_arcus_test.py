"""
ArcusRawIncrementMotionAdapter over the fake controller (real time, short
moves), and the increments published by ArcusAdapter's monitor without any
mm conversion.
"""

import queue
import time
import unittest

from application.services.raw_increment_motion.ports.raw_increment_motion_error import (
    RawIncrementMotionError,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.hardware.arcus_performax_4EX.adapter_raw_increment_motion_arcus import (
    ArcusRawIncrementMotionAdapter,
)
from infrastructure.hardware.arcus_performax_4EX.fake.fake_arcus_performax4ex_controller import (
    FakeArcusPerformax4EXController,
)


class ArcusRawIncrementMotionAdapterTest(unittest.TestCase):
    def setUp(self):
        self.controller = FakeArcusPerformax4EXController()
        self.controller.connect()
        self.controller.plus_limit_increments = 600  # short travel: real-time test
        self.port = ArcusRawIncrementMotionAdapter(self.controller)

    def test_home_sets_the_origin(self):
        self.controller.set_position_reference("x", 1234)
        self.port.home("X")
        self.assertEqual(self.port.get_position("X"), 0)

    def test_move_to_an_increment_without_any_conversion(self):
        self.port.home("X")
        self.port.set_speed("X", 3000)
        self.port.move_to("X", 300)
        self.assertTrue(self.port.is_moving("X"))
        self.port.wait_until_stopped("X", timeout_s=5.0)
        self.assertEqual(self.port.get_position("X"), 300)
        self.assertFalse(self.port.is_at_positive_limit("X"))

    def test_run_to_positive_limit_stops_on_the_switch(self):
        self.port.home("Y")
        self.port.set_speed("Y", 3000)
        self.port.run_to_positive_limit("Y")
        self.port.wait_until_stopped("Y", timeout_s=5.0)
        self.assertEqual(self.port.get_position("Y"), 600)
        self.assertTrue(self.port.is_at_positive_limit("Y"))

    def test_stop_freezes_the_axis(self):
        self.port.home("X")
        self.port.set_speed("X", 800)
        self.port.run_to_positive_limit("X")
        time.sleep(0.3)
        self.port.stop("X")
        stopped = self.port.get_position("X")
        self.assertFalse(self.port.is_moving("X"))
        self.assertLess(stopped, 600)

    def test_driver_failures_become_the_port_error(self):
        self.controller.disconnect()
        with self.assertRaises(RawIncrementMotionError):
            self.port.get_position("X")
        with self.assertRaises(RawIncrementMotionError):
            self.port.home("X")

    def test_moving_before_homing_is_refused_by_the_controller(self):
        with self.assertRaises(RawIncrementMotionError):
            self.port.move_to("X", 10)

    def test_wait_times_out_with_the_port_error(self):
        self.port.home("X")
        self.port.set_speed("X", 10)
        self.port.move_to("X", 500)
        with self.assertRaises(RawIncrementMotionError):
            self.port.wait_until_stopped("X", timeout_s=0.1)
        self.port.stop("X")


class MonitorPublishesIncrementsTest(unittest.TestCase):
    def test_increments_are_published_without_mm_conversion(self):
        bus = InMemoryEventBus()
        increments, positions = queue.Queue(), queue.Queue()
        bus.subscribe("motorincrementsupdated", increments.put)
        bus.subscribe("positionupdated", positions.put)
        controller = FakeArcusPerformax4EXController()
        controller.connect()
        controller.home_both()
        controller.set_position_reference("x", 123)
        adapter = ArcusAdapter(event_bus=bus)
        adapter.set_controller(controller)
        adapter.enable()
        try:
            event = increments.get(timeout=2.0)
            self.assertEqual((event.x_increments, event.y_increments), (123, 0))
            controller.set_position_reference("y", 77)
            event = increments.get(timeout=2.0)
            self.assertEqual((event.x_increments, event.y_increments), (123, 77))
            self.assertTrue(positions.empty())  # no mm without conversion
            adapter.set_microns_per_pulse(10.0)
            self.assertAlmostEqual(positions.get(timeout=2.0).position.x, 1.23)
        finally:
            adapter.disable()


if __name__ == "__main__":
    unittest.main()
