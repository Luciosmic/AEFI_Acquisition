import dataclasses

import pytest

from application.services.inertial_sensor_service.dtos.inertial_sensor_dtos import (
    ALL_CHANNELS,
    InertialSensorAcquisitionConfig,
    InertialSensorStreamSample,
)


def test_all_channels_but_timestamp_are_optional():
    s = InertialSensorStreamSample(timestamp_s=1.5)
    assert s.acceleration_g is None and s.angular_rate_dps is None and s.magnetic_field_ut is None
    assert s.lidar_raw is None and s.lidar_distance_mm is None


def test_sample_is_frozen():
    s = InertialSensorStreamSample(timestamp_s=0.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.timestamp_s = 1.0


def test_config_defaults_to_every_channel():
    assert InertialSensorAcquisitionConfig().channels == ALL_CHANNELS
    assert set(ALL_CHANNELS) == {"accelerometer", "gyroscope", "magnetometer", "lidar"}
