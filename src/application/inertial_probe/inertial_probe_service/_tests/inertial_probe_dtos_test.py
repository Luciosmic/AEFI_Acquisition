import dataclasses

import pytest

from application.inertial_probe.inertial_probe_service.dtos.inertial_probe_dtos import (
    ALL_CHANNELS,
    InertialProbeAcquisitionConfig,
    InertialProbeStreamSample,
)


def test_all_channels_but_timestamp_are_optional():
    s = InertialProbeStreamSample(timestamp_s=1.5)
    assert s.acceleration_g is None and s.angular_rate_dps is None and s.magnetic_field_ut is None
    assert s.lidar_distance is None


def test_sample_is_frozen():
    s = InertialProbeStreamSample(timestamp_s=0.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.timestamp_s = 1.0


def test_config_defaults_to_every_channel():
    assert InertialProbeAcquisitionConfig().channels == ALL_CHANNELS
    assert set(ALL_CHANNELS) == {"accelerometer", "gyroscope", "magnetometer", "lidar"}
