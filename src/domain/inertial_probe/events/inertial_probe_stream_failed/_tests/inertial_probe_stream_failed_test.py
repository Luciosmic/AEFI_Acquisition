"""Caractérisation de inertial_probe_stream_failed : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.inertial_probe.events.inertial_probe_stream_failed.inertial_probe_stream_failed import InertialProbeStreamFailed
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_inertialprobestreamfailed_garde_ses_champs() -> None:
    acquisition_id = UUID(int=1)
    reason = "x"
    instance = InertialProbeStreamFailed(acquisition_id=acquisition_id, reason=reason)
    assert isinstance(instance, DomainEvent)
    assert instance.acquisition_id == acquisition_id
    assert instance.reason == reason


def test_inertialprobestreamfailed_est_immuable() -> None:
    acquisition_id = UUID(int=1)
    reason = "x"
    instance = InertialProbeStreamFailed(acquisition_id=acquisition_id, reason=reason)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.acquisition_id = acquisition_id
