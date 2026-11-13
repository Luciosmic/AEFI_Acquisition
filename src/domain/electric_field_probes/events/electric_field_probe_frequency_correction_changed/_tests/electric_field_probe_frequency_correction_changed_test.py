"""Caractérisation de electric_field_probe_frequency_correction_changed : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.electric_field_probes.events.electric_field_probe_frequency_correction_changed.electric_field_probe_frequency_correction_changed import ElectricFieldProbeFrequencyCorrectionChanged
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_electricfieldprobefrequencycorrectionchanged_garde_ses_champs() -> None:
    requested_hz = 1.5
    applied_hz = None
    in_range = True
    instance = ElectricFieldProbeFrequencyCorrectionChanged(requested_hz=requested_hz, applied_hz=applied_hz, in_range=in_range)
    assert isinstance(instance, DomainEvent)
    assert instance.requested_hz == requested_hz
    assert instance.applied_hz == applied_hz
    assert instance.in_range == in_range


def test_electricfieldprobefrequencycorrectionchanged_est_immuable() -> None:
    requested_hz = 1.5
    applied_hz = None
    in_range = True
    instance = ElectricFieldProbeFrequencyCorrectionChanged(requested_hz=requested_hz, applied_hz=applied_hz, in_range=in_range)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.requested_hz = requested_hz
