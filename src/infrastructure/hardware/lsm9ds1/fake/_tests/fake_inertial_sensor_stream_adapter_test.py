import pytest

from infrastructure.hardware.lsm9ds1.fake.fake_inertial_sensor_stream_adapter import (
    FakeInertialSensorStreamAdapter,
)

ALL = ["accelerometer", "gyroscope", "magnetometer", "lidar"]


def _drain(f, n):
    return [f.read_sample() for _ in range(n)]


def test_requires_connect_and_start():
    f = FakeInertialSensorStreamAdapter(realtime=False)
    with pytest.raises(RuntimeError):
        f.start_stream(ALL)
    f.connect()
    with pytest.raises(RuntimeError):
        f.read_sample()


def test_lidar_caps_rate_at_25_hz_with_regular_timestamps():
    f = FakeInertialSensorStreamAdapter(rate_hz=100, realtime=False)
    f.connect()
    f.start_stream(ALL)
    s = _drain(f, 26)
    assert s[25].timestamp_s - s[0].timestamp_s == pytest.approx(1.0)


def test_accelerometer_only_runs_at_requested_rate():
    f = FakeInertialSensorStreamAdapter(rate_hz=100, realtime=False)
    f.connect()
    f.start_stream(["accelerometer"])
    s = _drain(f, 101)
    assert s[100].timestamp_s - s[0].timestamp_s == pytest.approx(1.0)


def test_only_requested_channels_are_filled():
    f = FakeInertialSensorStreamAdapter(realtime=False)
    f.connect()
    f.start_stream(["accelerometer", "lidar"])
    s = f.read_sample()
    assert s.acceleration_g is not None and s.lidar_distance_mm is not None
    assert s.angular_rate_dps is None and s.magnetic_field_ut is None


def test_deterministic_and_gravity_norm_one_g():
    a, b = FakeInertialSensorStreamAdapter(realtime=False), FakeInertialSensorStreamAdapter(realtime=False)
    for f in (a, b):
        f.connect()
        f.start_stream(ALL)
    for _ in range(5):
        sa, sb = a.read_sample(), b.read_sample()
        assert sa == sb
        assert sum(c * c for c in sa.acceleration_g) ** 0.5 == pytest.approx(1.0)


def test_stop_then_read_raises_and_simulated_connection_failure():
    f = FakeInertialSensorStreamAdapter(realtime=False)
    f.connect()
    f.start_stream(ALL)
    f.stop_stream()
    with pytest.raises(RuntimeError):
        f.read_sample()
    g = FakeInertialSensorStreamAdapter(simulate_connection_failure=True)
    with pytest.raises(TimeoutError):
        g.connect()


def test_read_failure_after_n_samples_raises_oserror():
    f = FakeInertialSensorStreamAdapter(realtime=False, fail_after_samples=2)
    f.connect()
    f.start_stream(ALL)
    _drain(f, 2)
    with pytest.raises(OSError):
        f.read_sample()


def test_stall_after_n_samples_returns_none_like_a_silent_board():
    f = FakeInertialSensorStreamAdapter(realtime=False, stall_after_samples=2)
    f.connect()
    f.start_stream(ALL)
    _drain(f, 2)
    assert f.read_sample() is None


def test_disconnect_is_idempotent():
    f = FakeInertialSensorStreamAdapter(realtime=False)
    f.connect()
    f.disconnect()
    f.disconnect()
    assert not f.is_connected()
