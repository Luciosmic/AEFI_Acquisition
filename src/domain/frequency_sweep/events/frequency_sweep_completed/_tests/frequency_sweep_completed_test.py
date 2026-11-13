"""Caractérisation de frequency_sweep_completed : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.frequency_sweep.events.frequency_sweep_completed.frequency_sweep_completed import FrequencySweepCompleted
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_frequencysweepcompleted_garde_ses_champs() -> None:
    frequency_sweep_id = UUID(int=1)
    role = "x"
    frequency_count = 3
    instance = FrequencySweepCompleted(frequency_sweep_id=frequency_sweep_id, role=role, frequency_count=frequency_count)  # type: ignore[arg-type]
    assert isinstance(instance, DomainEvent)
    assert instance.frequency_sweep_id == frequency_sweep_id
    assert instance.role == role
    assert instance.frequency_count == frequency_count


def test_frequencysweepcompleted_est_immuable() -> None:
    frequency_sweep_id = UUID(int=1)
    role = "x"
    frequency_count = 3
    instance = FrequencySweepCompleted(frequency_sweep_id=frequency_sweep_id, role=role, frequency_count=frequency_count)  # type: ignore[arg-type]
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.frequency_sweep_id = frequency_sweep_id  # type: ignore[assignment,misc]
