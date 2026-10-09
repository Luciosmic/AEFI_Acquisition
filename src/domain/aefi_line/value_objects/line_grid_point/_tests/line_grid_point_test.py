import dataclasses
from datetime import datetime, timezone

import pytest

from domain.aefi_line.value_objects.line_grid_point.line_grid_point import LineGridPoint
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D

M = AefiVoltageMeasurement(1, 1, 1, 1, 1, 1, timestamp=datetime(2026, 10, 9, tzinfo=timezone.utc))


def test_frozen_value_object():
    point = LineGridPoint(0, Position2D(0.0, 1.0), M)
    with pytest.raises(dataclasses.FrozenInstanceError):
        point.index_in_line = 1
    assert point == LineGridPoint(0, Position2D(0.0, 1.0), M)


def test_index_must_not_be_negative():
    with pytest.raises(ValueError):
        LineGridPoint(-1, Position2D(0.0, 1.0), M)
