"""
Arcus adapter and lifecycle with no mm/pulse conversion (mechanical
transmission not calibrated): the stack starts, the controller is verified in
pulses, motion is refused with a typed error and the monitor stays quiet.
"""

import logging
import time
import unittest

from application.services.motion_control_service.ports.motion_conversion_unavailable_error import (
    MotionConversionUnavailableError,
)
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from infrastructure.hardware.arcus_performax_4EX.adapter_lifecycle_arcus_performax4EX import (
    ArcusPerformaxLifecycleAdapter,
)
from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.hardware.arcus_performax_4EX.fake.fake_arcus_performax4ex_controller import (
    FakeArcusPerformax4EXController,
)


class UncalibratedAdapterTest(unittest.TestCase):
    def setUp(self):
        self.controller = FakeArcusPerformax4EXController()
        self.controller.connect()
        self.adapter = ArcusAdapter()
        self.adapter.set_controller(self.controller)

    def test_conversion_is_reported_unavailable_until_applied(self):
        self.assertFalse(self.adapter.is_conversion_available())
        self.adapter.set_microns_per_pulse(21.8)
        self.assertTrue(self.adapter.is_conversion_available())

    def test_move_to_raises_typed_error(self):
        with self.assertRaises(MotionConversionUnavailableError) as raised:
            self.adapter.move_to(Position2D(x=1.0, y=1.0))
        self.assertEqual(raised.exception.operation, "move_to")

    def test_set_speed_raises_typed_error(self):
        with self.assertRaises(MotionConversionUnavailableError):
            self.adapter.set_speed(5.0)

    def test_position_in_mm_raises_typed_error(self):
        with self.assertRaises(MotionConversionUnavailableError):
            self.adapter.get_current_position()

    def test_typed_error_stays_a_runtime_error(self):
        with self.assertRaises(RuntimeError):
            self.adapter.move_to(Position2D(x=1.0, y=1.0))

    def test_stop_stays_available(self):
        self.adapter.emergency_stop()

    def test_speed_mode_in_pulses_stays_available(self):
        self.adapter.set_speed_mode("slow")

    def test_monitor_loop_logs_one_warning_and_no_traceback(self):
        records = []

        class Collector(logging.Handler):
            def emit(self, record):
                records.append(record)

        handler = Collector(level=logging.DEBUG)
        logger = logging.getLogger("infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX")
        previous_level = logger.level
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        try:
            self.adapter.enable()
            time.sleep(2.3)  # at least two monitor cycles (1 s each when uncalibrated)
            self.adapter.disable()
        finally:
            logger.removeHandler(handler)
            logger.setLevel(previous_level)

        warnings = [r for r in records if r.levelno >= logging.WARNING]
        self.assertEqual(len(warnings), 1, [r.getMessage() for r in warnings])
        self.assertIn("no mm/pulse conversion", warnings[0].getMessage())
        self.assertEqual([r for r in records if r.exc_info], [])


class UncalibratedLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.controller = FakeArcusPerformax4EXController()
        self.adapter = ArcusAdapter()
        self.lifecycle = ArcusPerformaxLifecycleAdapter(self.adapter, self.controller)

    def tearDown(self):
        self.lifecycle.close_all()

    def test_startup_verifies_without_conversion(self):
        self.lifecycle.initialize_all()
        self.assertFalse(self.adapter.is_conversion_available())
        self.assertTrue(self.lifecycle.verify_all())

    def test_verification_fails_when_controller_does_not_answer(self):
        self.lifecycle.initialize_all()
        self.controller.disconnect()
        with self.assertRaises(RuntimeError):
            self.lifecycle.verify_all()


if __name__ == "__main__":
    unittest.main()
