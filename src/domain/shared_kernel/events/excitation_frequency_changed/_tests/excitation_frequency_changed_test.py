"""Caractérisation de excitation_frequency_changed : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.excitation_frequency_changed.excitation_frequency_changed import ExcitationFrequencyChanged


def test_excitationfrequencychanged_garde_ses_champs() -> None:
    frequency_hz = 1.5
    instance = ExcitationFrequencyChanged(frequency_hz=frequency_hz)
    assert isinstance(instance, DomainEvent)
    assert instance.frequency_hz == frequency_hz


def test_excitationfrequencychanged_est_immuable() -> None:
    frequency_hz = 1.5
    instance = ExcitationFrequencyChanged(frequency_hz=frequency_hz)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.frequency_hz = frequency_hz  # type: ignore[misc]
