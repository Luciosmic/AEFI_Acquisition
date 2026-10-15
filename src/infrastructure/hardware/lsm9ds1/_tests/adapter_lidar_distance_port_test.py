import dataclasses
import time
import unittest

from application.services.lidar_distance.ports.lidar_stream_error import (
    LidarStreamBusyError,
    LidarUnavailableError,
)
from domain.shared_kernel.value_objects.lidar_distance.lidar_distance import LidarDistance
from infrastructure.hardware.lsm9ds1.adapter_lidar_distance_port import LidarDistanceStreamAdapter
from infrastructure.hardware.lsm9ds1.fake.fake_inertial_sensor_stream_adapter import (
    FakeInertialSensorStreamAdapter,
)


class _ZeroEveryOtherStream(FakeInertialSensorStreamAdapter):
    """The real LIDAR sends raw 0 when it measures nothing."""

    def read_sample(self, timeout_s=1.0):
        sample = super().read_sample(timeout_s)
        if sample is not None and self._k % 2 == 0:
            sample = dataclasses.replace(sample, lidar_distance=LidarDistance.from_raw(0, 1.0))
        return sample


class _Executor:
    def __init__(self, running=False):
        self.running = running

    def is_running(self):
        return self.running


class LidarDistanceStreamAdapterTest(unittest.TestCase):
    def test_opens_reads_timestamped_distances_and_closes(self):
        stream = FakeInertialSensorStreamAdapter(rate_hz=200.0, realtime=True)
        adapter = LidarDistanceStreamAdapter(stream, _Executor())
        adapter.open()
        try:
            self.assertTrue(stream.is_connected())  # connected by the calibration itself
            first = adapter.read_distance(1.0)
            second = adapter.read_distance(1.0)
            self.assertIsNotNone(first)
            self.assertGreater(first.distance.distance_mm, 1000.0)
            self.assertGreater(second.timestamp_s, first.timestamp_s)
        finally:
            adapter.close()
        self.assertFalse(stream.is_connected())  # disconnected again: it was not connected before

    def test_readings_keep_their_arrival_time_while_nobody_reads(self):
        stream = FakeInertialSensorStreamAdapter(rate_hz=25.0, realtime=True)
        adapter = LidarDistanceStreamAdapter(stream, _Executor())
        adapter.open()
        try:
            time.sleep(0.3)  # settling: nobody reads
            settled_at = time.perf_counter()
            buffered = adapter.read_distance(1.0)
            self.assertLess(buffered.timestamp_s, settled_at)
        finally:
            adapter.close()

    def test_raw_zero_is_a_reading_without_return_never_a_distance(self):
        adapter = LidarDistanceStreamAdapter(_ZeroEveryOtherStream(rate_hz=200.0, realtime=True), _Executor())
        adapter.open()
        try:
            readings = [adapter.read_distance(1.0) for _ in range(6)]
        finally:
            adapter.close()
        self.assertEqual([r.distance.has_return for r in readings], [True, False] * 3)

    def test_leaves_an_already_connected_board_connected(self):
        stream = FakeInertialSensorStreamAdapter(realtime=False)
        stream.connect()
        adapter = LidarDistanceStreamAdapter(stream, _Executor())
        adapter.open()
        adapter.close()
        self.assertTrue(stream.is_connected())

    def test_refuses_while_the_panel_streams(self):
        adapter = LidarDistanceStreamAdapter(FakeInertialSensorStreamAdapter(realtime=False), _Executor(running=True))
        self.assertTrue(adapter.is_streamed_elsewhere())
        with self.assertRaises(LidarStreamBusyError):
            adapter.open()

    def test_connection_failure_is_the_port_error(self):
        adapter = LidarDistanceStreamAdapter(FakeInertialSensorStreamAdapter(simulate_connection_failure=True), None)
        with self.assertRaises(LidarUnavailableError):
            adapter.open()

    def test_read_failures_become_the_port_error(self):
        stream = FakeInertialSensorStreamAdapter(realtime=False, fail_after_samples=3)
        adapter = LidarDistanceStreamAdapter(stream, _Executor())
        adapter.open()
        try:
            with self.assertRaises(LidarUnavailableError):
                for _ in range(10):
                    adapter.read_distance(0.5)
        finally:
            adapter.close()

    def test_close_is_idempotent(self):
        adapter = LidarDistanceStreamAdapter(FakeInertialSensorStreamAdapter(realtime=False), None)
        adapter.close()
        adapter.open()
        adapter.close()
        adapter.close()


if __name__ == "__main__":
    unittest.main()
