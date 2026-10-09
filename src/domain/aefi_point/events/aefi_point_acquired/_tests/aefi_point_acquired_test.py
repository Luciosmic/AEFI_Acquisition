import dataclasses
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.aefi_point.events.aefi_point_acquired.aefi_point_acquired import AefiPointAcquired
from domain.aefi_point.value_objects.aefi_point_id.aefi_point_id import AefiPointId
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


def test_event_is_a_frozen_domain_event_with_timestamp():
    m = AefiVoltageMeasurement(0, 0, 0, 0, 0, 0, timestamp=datetime(2026, 10, 9, tzinfo=timezone.utc))
    event = AefiPointAcquired(AefiPointId(uuid4()), uuid4(), Position2D(0, 0), m, 5)
    assert isinstance(event, DomainEvent)
    assert event.occurred_on is not None
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.samples_count = 1
