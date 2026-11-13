import math
from datetime import datetime

import pytest

from domain.detection_devices.electric_field_probes.value_objects.field_measurement.field_measurement import (
    FieldMeasurement,
)


def test_norm_is_computed_from_components() -> None:
    m = FieldMeasurement(components=(3.0, 4.0), timestamp=datetime.now())
    assert m.norm == pytest.approx(5.0)


def test_norm_supports_single_axis() -> None:
    m = FieldMeasurement(components=(2.0,), timestamp=datetime.now())
    assert m.norm == pytest.approx(2.0)


def test_rejects_empty_components() -> None:
    with pytest.raises(ValueError):
        FieldMeasurement(components=(), timestamp=datetime.now())


def test_rejects_non_finite_component() -> None:
    with pytest.raises(ValueError):
        FieldMeasurement(components=(1.0, math.inf), timestamp=datetime.now())


def test_is_frozen() -> None:
    m = FieldMeasurement(components=(1.0,), timestamp=datetime.now())
    with pytest.raises(Exception):
        m.components = (2.0,)


def test_std_dev_components_validation() -> None:
    """Test that std_dev_components must match components length."""
    with pytest.raises(ValueError):
        FieldMeasurement(
            components=(1.0, 2.0),
            timestamp=datetime.now(),
            std_dev_components=(0.1,)  # Wrong length
        )


def test_std_dev_components_with_valid_data() -> None:
    """Test that valid std_dev_components is accepted."""
    m = FieldMeasurement(
        components=(1.0, 2.0),
        timestamp=datetime.now(),
        std_dev_components=(0.1, 0.2)
    )
    assert m.std_dev_components == (0.1, 0.2)


def test_std_dev_components_rejects_non_finite() -> None:
    """Test that std_dev_components rejects non-finite values."""
    with pytest.raises(ValueError):
        FieldMeasurement(
            components=(1.0, 2.0),
            timestamp=datetime.now(),
            std_dev_components=(0.1, math.inf)
        )
