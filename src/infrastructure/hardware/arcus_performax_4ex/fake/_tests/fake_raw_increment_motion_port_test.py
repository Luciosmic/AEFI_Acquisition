import unittest

from application.test_bench.raw_increment_motion.ports.raw_increment_motion_error import (
    RawIncrementMotionError,
)
from infrastructure.execution.fake.fake_clock import FakeClock
from infrastructure.hardware.arcus_performax_4ex.fake.fake_raw_increment_motion_port import (
    FakeRawIncrementMotionPort,
)


class FakeRawIncrementMotionPortTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.port = FakeRawIncrementMotionPort(clock=self.clock, plus_limit_increments=8000)
        self.port.home("X")

    def test_moves_linearly_in_time_at_the_set_speed(self):
        self.port.set_speed("X", 1000)
        self.port.move_to("X", 2000)
        self.clock.sleep(1.0)
        self.assertEqual(self.port.get_position("X"), 1000)
        self.assertTrue(self.port.is_moving("X"))
        self.clock.sleep(1.5)
        self.assertEqual(self.port.get_position("X"), 2000)
        self.assertFalse(self.port.is_moving("X"))

    def test_runs_to_the_positive_limit_switch(self):
        self.port.set_speed("X", 4000)
        self.port.run_to_positive_limit("X")
        self.port.wait_until_stopped("X", timeout_s=10.0)
        self.assertEqual(self.port.get_position("X"), 8000)
        self.assertTrue(self.port.is_at_positive_limit("X"))
        self.assertAlmostEqual(self.clock.now(), 2.0, delta=0.05)

    def test_axis_stopping_without_switch_reads_no_limit(self):
        port = FakeRawIncrementMotionPort(clock=self.clock, plus_limit_increments=100, limit_switch_present=False)
        port.home("Y")
        port.run_to_positive_limit("Y")
        port.wait_until_stopped("Y", timeout_s=10.0)
        self.assertFalse(port.is_at_positive_limit("Y"))

    def test_stop_freezes_mid_move(self):
        self.port.set_speed("X", 1000)
        self.port.move_to("X", 5000)
        self.clock.sleep(0.5)
        self.port.stop("X")
        self.clock.sleep(1.0)
        self.assertEqual(self.port.get_position("X"), 500)

    def test_wait_times_out(self):
        self.port.set_speed("X", 10)
        self.port.move_to("X", 5000)
        with self.assertRaises(RawIncrementMotionError):
            self.port.wait_until_stopped("X", timeout_s=1.0)

    def test_simulated_failure_raises_the_port_error(self):
        port = FakeRawIncrementMotionPort(clock=self.clock, fail_on={"home"})
        with self.assertRaises(RawIncrementMotionError):
            port.home("X")


if __name__ == "__main__":
    unittest.main()
