import dataclasses
from uuid import uuid4

import pytest

from domain.aefi_line.events.aefi_line_abandoned.aefi_line_abandoned import AefiLineAbandoned
from domain.shared_kernel.events.domain_event import DomainEvent


def test_frozen_domain_event_carrying_the_abandoned_line():
    event = AefiLineAbandoned(uuid4(), 2, "paused", 3)
    assert isinstance(event, DomainEvent)
    assert (event.line_index, event.reason, event.discarded_points) == (2, "paused", 3)
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.line_index = 3
