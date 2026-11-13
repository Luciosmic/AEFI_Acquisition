import dataclasses
from uuid import uuid4

import pytest

from domain.detection_devices.inertial_probe.events.inertial_probe_connection_changed.inertial_probe_connection_changed import (
    InertialProbeConnectionChanged,
)
from domain.detection_devices.inertial_probe.events.inertial_probe_sample_acquired.inertial_probe_sample_acquired import (
    InertialProbeSampleAcquired,
)
from domain.detection_devices.inertial_probe.events.inertial_probe_stream_failed.inertial_probe_stream_failed import (
    InertialProbeStreamFailed,
)


def test_sample_event_channels_are_optional_and_frozen() -> None:
    e = InertialProbeSampleAcquired(acquisition_id=uuid4(), sample_index=0, timestamp_s=1.0)
    assert e.acceleration_g is None and e.lidar_distance is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.sample_index = 1


def test_connection_event_error_defaults_to_none() -> None:
    assert InertialProbeConnectionChanged(connected=True).error is None


def test_stream_failed_carries_acquisition_and_reason() -> None:
    acquisition_id = uuid4()
    e = InertialProbeStreamFailed(acquisition_id=acquisition_id, reason="boom")
    assert (e.acquisition_id, e.reason) == (acquisition_id, "boom")
