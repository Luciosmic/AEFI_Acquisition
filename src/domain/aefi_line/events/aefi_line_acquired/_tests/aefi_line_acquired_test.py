import dataclasses
from uuid import uuid4

import pytest

from domain.aefi_line.events.aefi_line_acquired.aefi_line_acquired import AefiLineAcquired
from domain.aefi_line.value_objects.aefi_line_id.aefi_line_id import AefiLineId
from domain.scan.events.probe_acquisition_event.probe_acquisition_event import ProbeAcquisitionEvent
from domain.shared_kernel.events.domain_event import DomainEvent


def test_frozen_domain_event_respecting_the_probe_contract():
    line_id = AefiLineId(uuid4())
    event = AefiLineAcquired(line_id, uuid4(), 2, (), 0)
    assert isinstance(event, DomainEvent) and isinstance(event, ProbeAcquisitionEvent)
    assert event.source == "aefi_line" and event.acquisition_id == line_id
    assert event.measurement_unit.endswith("/V")
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.line_index = 3
