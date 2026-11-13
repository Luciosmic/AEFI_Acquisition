from datetime import datetime

import pytest

from domain.electric_field_probe.electric_field_probe import ElectricFieldProbe


def _probe(axis_labels=("X", "Y", "Z")):
    return ElectricFieldProbe(
        brand="Narda", model="EP-601", serial_number="SN123", axis_labels=axis_labels
    )


def test_record_measurement_matches_axis_count():
    probe = _probe()
    m = probe.record_measurement((1.0, 2.0, 3.0), timestamp=datetime.now())
    assert m.components == (1.0, 2.0, 3.0)


def test_record_measurement_rejects_wrong_dimensionality():
    probe = _probe(axis_labels=("X", "Y", "Z"))
    with pytest.raises(ValueError):
        probe.record_measurement((1.0, 2.0), timestamp=datetime.now())


def test_supports_mono_axial_probe():
    probe = _probe(axis_labels=("X",))
    m = probe.record_measurement((1.0,), timestamp=datetime.now())
    assert m.components == (1.0,)


def test_carries_probe_identity():
    probe = _probe()
    assert probe.brand == "Narda"
    assert probe.model == "EP-601"
    assert probe.serial_number == "SN123"
