import unittest

from application.services.bar_transmission_calibration_service.ports.lidar_stream_error import (
    LidarStreamBusyError,
    LidarUnavailableError,
)
from infrastructure.execution.fake.fake_clock import FakeClock
from infrastructure.hardware.lsm9ds1.fake.fake_lidar_distance_port import SAMPLE_PERIOD_S, FakeLidarDistancePort


class FakeLidarDistancePortTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.port = FakeLidarDistancePort(lambda: 250.0, self.clock)

    def test_one_distance_per_sample_period(self):
        self.port.open()
        first, second = self.port.read_distance(1.0), self.port.read_distance(1.0)
        self.assertAlmostEqual(second.timestamp_s - first.timestamp_s, SAMPLE_PERIOD_S)
        self.assertEqual(first.distance_mm, 250.0)
        self.assertAlmostEqual(self.clock.now(), 2 * SAMPLE_PERIOD_S)

    def test_short_timeout_returns_none(self):
        self.port.open()
        self.assertIsNone(self.port.read_distance(0.0))

    def test_readings_arrived_while_nobody_read_keep_their_arrival_time(self):
        self.port.open()
        self.clock.sleep(0.5)
        reading = self.port.read_distance(0.0)
        self.assertLess(reading.timestamp_s, 0.5)

    def test_failure_modes(self):
        with self.assertRaises(LidarStreamBusyError):
            FakeLidarDistancePort(lambda: 1.0, self.clock, streamed_elsewhere=True).open()
        with self.assertRaises(LidarUnavailableError):
            FakeLidarDistancePort(lambda: 1.0, self.clock, fail_on_open=True).open()
        with self.assertRaises(LidarUnavailableError):
            self.port.read_distance(1.0)  # not open
        silent = FakeLidarDistancePort(lambda: 1.0, self.clock, silent_after_samples=1)
        silent.open()
        self.assertIsNotNone(silent.read_distance(1.0))
        self.assertIsNone(silent.read_distance(1.0))

    def test_counts_open_and_close(self):
        self.port.open()
        self.port.close()
        self.port.close()
        self.assertEqual((self.port.open_count, self.port.close_count), (1, 1))


if __name__ == "__main__":
    unittest.main()
