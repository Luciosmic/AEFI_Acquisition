"""Caractérisation de inertial_probe_sample_acquired : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.inertial_probe.events.inertial_probe_sample_acquired.inertial_probe_sample_acquired import InertialProbeSampleAcquired
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_inertialprobesampleacquired_garde_ses_champs() -> None:
    acquisition_id = UUID(int=1)
    sample_index = 3
    timestamp_s = 1.5
    instance = InertialProbeSampleAcquired(acquisition_id=acquisition_id, sample_index=sample_index, timestamp_s=timestamp_s)
    assert isinstance(instance, DomainEvent)
    assert instance.acquisition_id == acquisition_id
    assert instance.sample_index == sample_index
    assert instance.timestamp_s == timestamp_s


def test_inertialprobesampleacquired_est_immuable() -> None:
    acquisition_id = UUID(int=1)
    sample_index = 3
    timestamp_s = 1.5
    instance = InertialProbeSampleAcquired(acquisition_id=acquisition_id, sample_index=sample_index, timestamp_s=timestamp_s)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.acquisition_id = acquisition_id  # type: ignore[misc]
