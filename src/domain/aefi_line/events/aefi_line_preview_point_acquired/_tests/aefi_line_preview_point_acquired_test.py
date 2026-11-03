import dataclasses
from uuid import uuid4

import pytest

from domain.aefi_line.events.aefi_line_preview_point_acquired.aefi_line_preview_point_acquired import (
    AefiLinePreviewPointAcquired,
)
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


def test_frozen_provisional_domain_event():
    event = AefiLinePreviewPointAcquired(uuid4(), 1, 2, Position2D(x=1.0, y=2.0), object())
    assert isinstance(event, DomainEvent)
    assert (event.line_index, event.index_in_line) == (1, 2)
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.line_index = 3
