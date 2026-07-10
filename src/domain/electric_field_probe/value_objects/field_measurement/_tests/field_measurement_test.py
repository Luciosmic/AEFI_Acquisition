import math
from datetime import datetime

import pytest

from domain.electric_field_probe.value_objects.field_measurement.field_measurement import (
    FieldMeasurement,
)


def test_norm_is_computed_from_components():
    m = FieldMeasurement(components=(3.0, 4.0), timestamp=datetime.now())
    assert m.norm == pytest.approx(5.0)


def test_norm_supports_single_axis():
    m = FieldMeasurement(components=(2.0,), timestamp=datetime.now())
    assert m.norm == pytest.approx(2.0)


def test_rejects_empty_components():
    with pytest.raises(ValueError):
        FieldMeasurement(components=(), timestamp=datetime.now())


def test_rejects_non_finite_component():
    with pytest.raises(ValueError):
        FieldMeasurement(components=(1.0, math.inf), timestamp=datetime.now())


def test_is_frozen():
    m = FieldMeasurement(components=(1.0,), timestamp=datetime.now())
    with pytest.raises(Exception):
        m.components = (2.0,)
