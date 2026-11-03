import dataclasses
from uuid import uuid4

import pytest

from domain.inertial_sensor.events.inertial_sensor_connection_changed.inertial_sensor_connection_changed import (
    InertialSensorConnectionChanged,
)
from domain.inertial_sensor.events.inertial_sensor_sample_acquired.inertial_sensor_sample_acquired import (
    InertialSensorSampleAcquired,
)
from domain.inertial_sensor.events.inertial_sensor_stream_failed.inertial_sensor_stream_failed import (
    InertialSensorStreamFailed,
)


def test_sample_event_channels_are_optional_and_frozen():
    e = InertialSensorSampleAcquired(acquisition_id=uuid4(), sample_index=0, timestamp_s=1.0)
    assert e.acceleration_g is None and e.lidar_distance_mm is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.sample_index = 1


def test_connection_event_error_defaults_to_none():
    assert InertialSensorConnectionChanged(connected=True).error is None


def test_stream_failed_carries_acquisition_and_reason():
    acquisition_id = uuid4()
    e = InertialSensorStreamFailed(acquisition_id=acquisition_id, reason="boom")
    assert (e.acquisition_id, e.reason) == (acquisition_id, "boom")
