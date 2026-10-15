from unittest.mock import MagicMock, patch

import pytest

from infrastructure.hardware.lsm9ds1.adapter_inertial_sensor_stream_port import (
    Lsm9ds1InertialSensorStreamAdapter,
)

DRIVER = "infrastructure.hardware.lsm9ds1.adapter_inertial_sensor_stream_port.LSM9DS1StreamDriver"
ALL = ["accelerometer", "gyroscope", "magnetometer", "lidar"]


@pytest.fixture
def driver():
    with patch(DRIVER) as cls:
        drv = MagicMock()
        cls.return_value = drv
        yield drv


def make():
    return Lsm9ds1InertialSensorStreamAdapter(port="COM5", baudrate=256000)


def test_converts_raw_to_physical_and_keeps_lidar_raw_and_mm(driver):
    driver.read_sample.return_value = (
        12.5,
        {
            "magnetometer": (0, 16384, 0),
            "accelerometer": (0, 0, 16384),
            "gyroscope": (16384, 0, 0),
            "lidar": (1250,),
        },
    )
    a = make()
    a.connect()
    a.start_stream(ALL)
    s = a.read_sample(timeout_s=1.0)
    assert s.timestamp_s == 12.5
    assert s.acceleration_g == (0.0, 0.0, 1.0)
    assert s.angular_rate_dps == (245.0, 0.0, 0.0)
    assert s.magnetic_field_ut == (0.0, 200.0, 0.0)
    assert s.lidar_raw == 1250 and s.lidar_distance_mm == 1250.0


def test_subset_leaves_other_channels_none(driver):
    driver.read_sample.return_value = (1.0, {"accelerometer": (0, 0, 16384)})
    a = make()
    a.connect()
    s = a.read_sample()
    assert s.angular_rate_dps is None and s.magnetic_field_ut is None
    assert s.lidar_distance_mm is None


def test_timeout_returns_none(driver):
    driver.read_sample.return_value = None
    a = make()
    a.connect()
    assert a.read_sample() is None


def test_no_rest_calibration_is_applied(driver):
    driver.read_sample.return_value = (1.0, {"accelerometer": (16384, 0, 0), "gyroscope": (0, 0, 0)})
    a = make()
    a.connect()
    s = a.read_sample()
    assert s.acceleration_g == (1.0, 0.0, 0.0)
    assert s.angular_rate_dps == (0.0, 0.0, 0.0)


def test_rate_is_forwarded_to_driver_when_configured(driver):
    a = Lsm9ds1InertialSensorStreamAdapter(port="COM5", baudrate=256000, rate_hz=50)
    a.connect()
    a.start_stream(["accelerometer"])
    driver.start_stream.assert_called_once_with(["accelerometer"], rate_hz=50)


def test_read_before_connect_raises(driver):
    with pytest.raises(RuntimeError):
        make().read_sample()


def test_disconnect_closes_driver(driver):
    a = make()
    a.connect()
    a.disconnect()
    driver.disconnect.assert_called_once()
    assert not a.is_connected()
