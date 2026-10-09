import dataclasses
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.electric_field_probe.value_objects.field_measurement.field_measurement import FieldMeasurement
from domain.narda_point.events.narda_point_acquired.narda_point_acquired import NardaPointAcquired
from domain.narda_point.value_objects.narda_point_id.narda_point_id import NardaPointId
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


def make_event(point_id=None):
    fm = FieldMeasurement((1.0, 2.0), datetime(2026, 10, 9, tzinfo=timezone.utc))
    return NardaPointAcquired(
        NardaPointId(point_id or uuid4()), uuid4(), 3, Position2D(0, 0), fm, None, ("X", "Y"), 5
    )


def test_event_is_a_frozen_domain_event_with_timestamp():
    event = make_event()
    assert isinstance(event, DomainEvent)
    assert event.occurred_on is not None
    assert event.measurement_unit.endswith("/V-PER-M")
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.samples_count = 1


def test_event_respects_the_probe_acquisition_contract():
    from domain.scan.events.probe_acquisition_event.probe_acquisition_event import ProbeAcquisitionEvent

    point_id = uuid4()
    event = make_event(point_id)
    assert isinstance(event, ProbeAcquisitionEvent)
    assert event.source == "narda_point" and event.acquisition_id == point_id
