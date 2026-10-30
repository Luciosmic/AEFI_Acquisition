import threading
import time
import unittest

from application.services.bar_transmission_calibration_service.ports.lidar_stream_error import (
    LidarUnavailableError,
)
from infrastructure.hardware.esp32_serial_lidar.adapter_lidar_distance_port import (
    Esp32SerialLidarAdapter,
    parse_raw_distance,
)


class _ScriptedSerial:
    """Serial port that delivers scripted chunks (bytes, or an exception to raise),
    then times out like pyserial (returns b"" after `timeout`)."""

    def __init__(self, chunks, timeout=0.01):
        self._chunks = list(chunks)
        self._timeout = timeout
        self._lock = threading.Lock()
        self.in_waiting = 0
        self.closed = False
        self.opened_with = None

    def push(self, *chunks):
        with self._lock:
            self._chunks.extend(chunks)

    def read(self, n=1):
        with self._lock:
            chunk = self._chunks.pop(0) if self._chunks else None
        if chunk is None:
            time.sleep(self._timeout)
            return b""
        if isinstance(chunk, Exception):
            raise chunk
        return chunk

    def reset_input_buffer(self):
        pass

    def close(self):
        self.closed = True


def _factory(ser):
    def make(port, baudrate, timeout):
        ser.opened_with = (port, baudrate)
        return ser
    return make


def _adapter(ser):
    return Esp32SerialLidarAdapter("COMX", 115200, serial_factory=_factory(ser))


class ParseRawDistanceTest(unittest.TestCase):
    def test_keeps_the_raw_column_and_ignores_the_moving_average(self):
        self.assertEqual(parse_raw_distance(b"1227 1230\r"), 1227)

    def test_unreadable_lines_are_none(self):
        for line in (b"", b"1227", b"1227 1230 5", b"abc 1230", b"1227 x", b"\xff\xfe 12"):
            self.assertIsNone(parse_raw_distance(line), line)


class Esp32SerialLidarAdapterTest(unittest.TestCase):
    def test_opens_the_given_port_reads_raw_distances_and_closes(self):
        ser = _ScriptedSerial([b"27 1230\r\n", b"1227 1230\r\n1240 12", b"31\r\n"])
        adapter = _adapter(ser)
        adapter.open()
        try:
            first = adapter.read_distance(1.0)
            second = adapter.read_distance(1.0)
        finally:
            adapter.close()
        self.assertEqual(ser.opened_with, ("COMX", 115200))
        # the first (mid-line) line is dropped; a line split across chunks is reassembled
        self.assertEqual([first.distance.distance_mm, second.distance.distance_mm], [1227.0, 1240.0])
        self.assertGreater(second.timestamp_s, first.timestamp_s)
        self.assertTrue(ser.closed)

    def test_readings_keep_their_arrival_time_while_nobody_reads(self):
        ser = _ScriptedSerial([b"x\r\n", b"1227 1230\r\n"])
        adapter = _adapter(ser)
        adapter.open()
        try:
            time.sleep(0.2)  # settling: nobody reads
            settled_at = time.perf_counter()
            buffered = adapter.read_distance(1.0)
            self.assertLess(buffered.timestamp_s, settled_at)
        finally:
            adapter.close()

    def test_raw_zero_is_a_reading_without_return_never_a_distance(self):
        ser = _ScriptedSerial([b"\r\n", b"1227 1230\r\n0 1100\r\n1229 1100\r\n"])
        adapter = _adapter(ser)
        adapter.open()
        try:
            readings = [adapter.read_distance(1.0) for _ in range(3)]
        finally:
            adapter.close()
        self.assertEqual([r.distance.has_return for r in readings], [True, False, True])

    def test_unreadable_lines_are_skipped_without_error(self):
        ser = _ScriptedSerial([b"\r\n", b"garbage\r\n1227\r\n" + b"z" * 100, b"\r\n1228 1230\r\n"])
        adapter = _adapter(ser)
        adapter.open()
        try:
            reading = adapter.read_distance(1.0)
            self.assertEqual(reading.distance.distance_mm, 1228.0)
            self.assertIsNone(adapter.read_distance(0.05))
        finally:
            adapter.close()

    def test_is_never_streamed_elsewhere(self):
        self.assertFalse(_adapter(_ScriptedSerial([])).is_streamed_elsewhere())

    def test_open_failure_is_the_port_error(self):
        def refuse(port, baudrate, timeout):
            raise OSError("could not open port 'COMX': PermissionError")
        adapter = Esp32SerialLidarAdapter("COMX", 115200, serial_factory=refuse)
        with self.assertRaises(LidarUnavailableError):
            adapter.open()

    def test_read_failures_become_the_port_error(self):
        ser = _ScriptedSerial([OSError("device unplugged")] * 5)
        adapter = _adapter(ser)
        adapter.open()
        try:
            with self.assertRaises(LidarUnavailableError):
                for _ in range(10):
                    adapter.read_distance(0.2)
        finally:
            adapter.close()

    def test_a_single_read_failure_is_tolerated(self):
        ser = _ScriptedSerial([b"\r\n", OSError("glitch"), b"1227 1230\r\n"])
        adapter = _adapter(ser)
        adapter.open()
        try:
            self.assertEqual(adapter.read_distance(1.0).distance.distance_mm, 1227.0)
        finally:
            adapter.close()

    def test_close_is_idempotent_and_reopen_works(self):
        ser = _ScriptedSerial([])
        adapter = _adapter(ser)
        adapter.close()
        adapter.open()
        adapter.close()
        adapter.close()
        ser.push(b"\r\n", b"1227 1230\r\n")
        adapter.open()
        try:
            self.assertEqual(adapter.read_distance(1.0).distance.distance_mm, 1227.0)
        finally:
            adapter.close()


if __name__ == "__main__":
    unittest.main()
