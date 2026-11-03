import dataclasses
import math
from datetime import datetime, timezone

import pytest

from domain.aefi_point.value_objects.sample.sample import Sample
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement

NOW = datetime(2026, 10, 9, tzinfo=timezone.utc)


def test_non_finite_voltage_cannot_become_a_sample():
    with pytest.raises(ValueError):
        Sample(AefiVoltageMeasurement(0, 0, 0, 0, 0, math.nan, timestamp=NOW))


def test_sample_is_immutable():
    sample = Sample(AefiVoltageMeasurement(0, 0, 0, 0, 0, 1.0, timestamp=NOW))
    with pytest.raises(dataclasses.FrozenInstanceError):
        sample.measurement = None
