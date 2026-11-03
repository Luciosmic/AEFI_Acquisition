import pytest

from infrastructure.hardware.lsm9ds1.driver_lsm9ds1_stream import LSM9DS1StreamDriver


class FakeStreamSerial:
    def __init__(self, chunks=()):
        self.chunks = list(chunks)
        self.written = []
        self.is_open = True
        self.resets = 0

    @property
    def in_waiting(self):
        return len(self.chunks[0]) if self.chunks else 0

    def read(self, n=1):
        return self.chunks.pop(0) if self.chunks else b""

    def write(self, data):
        self.written.append(data)

    def reset_input_buffer(self):
        self.resets += 1

    def close(self):
        self.is_open = False


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        self.t += 0.01
        return self.t


def make(chunks=()):
    ser = FakeStreamSerial(chunks)
    drv = LSM9DS1StreamDriver(
        port="COMX",
        baudrate=256000,
        serial_factory=lambda *a, **k: ser,
        sleep=lambda s: None,
        clock=Clock(),
    )
    drv.connect()
    return drv, ser


def test_connect_sends_stop_and_flushes_never_waits_for_reset():
    drv, ser = make()
    assert ser.written == [b"S*"]
    assert ser.resets == 1


def test_start_stream_sends_documented_sequence_without_line_feed():
    drv, ser = make()
    ser.written.clear()
    drv.start_stream(["accelerometer", "lidar"])
    assert ser.written == [b"S*", b"A9*", b"L9*"]
    assert all(b"\n" not in w for w in ser.written)


def test_rate_command_only_when_requested():
    drv, ser = make()
    ser.written.clear()
    drv.start_stream(["accelerometer"], rate_hz=50)
    assert b"F50*" in ser.written
    ser.written.clear()
    drv.start_stream(["accelerometer"])
    assert not any(w.startswith(b"F") for w in ser.written)


def test_rate_must_be_documented_value():
    drv, _ = make()
    with pytest.raises(ValueError):
        drv.start_stream(["accelerometer"], rate_hz=17)


def test_read_sample_parses_and_timestamps_at_reception():
    drv, ser = make()
    drv.start_stream(["accelerometer", "lidar"])
    ser.chunks = [b"16868\t-120\t1186\t1190\n", b"16870\t-121\t1180\t1191\n"]
    t1, d1 = drv.read_sample(timeout_s=1.0)
    t2, d2 = drv.read_sample(timeout_s=1.0)
    assert d1 == {"accelerometer": (16868, -120, 1186), "lidar": (1190,)}
    assert d2["lidar"] == (1191,)
    assert t2 > t1


def test_partial_lines_across_chunks_are_reassembled():
    drv, ser = make()
    drv.start_stream(["accelerometer"])
    ser.chunks = [b"16868\t-12", b"0\t1186\t\n"]
    _, d = drv.read_sample(timeout_s=1.0)
    assert d == {"accelerometer": (16868, -120, 1186)}


def test_out_of_regime_lines_are_dropped_and_counted():
    drv, ser = make()
    drv.start_stream(["accelerometer", "lidar"])
    ser.chunks = [b"1\t2\t3\t\n16868\t-120\t1186\t1190\n"]
    _, d = drv.read_sample(timeout_s=1.0)
    assert d["lidar"] == (1190,)
    assert drv.dropped_lines == 1


def test_read_timeout_returns_none():
    drv, ser = make()
    drv.start_stream(["accelerometer"])
    assert drv.read_sample(timeout_s=0.05) is None


def test_read_without_start_raises():
    drv, _ = make()
    with pytest.raises(RuntimeError):
        drv.read_sample(timeout_s=0.1)


def test_stop_and_disconnect_send_stop_and_flush():
    drv, ser = make()
    drv.start_stream(["accelerometer"])
    ser.written.clear()
    drv.stop_stream()
    assert ser.written == [b"S*"]
    drv.start_stream(["accelerometer"])
    ser.written.clear()
    drv.disconnect()
    assert ser.written == [b"S*"]
    assert not ser.is_open
    drv.disconnect()  # idempotent
