"""Caractérisation de scan_resumed : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.step_scan.events.scan_resumed.scan_resumed import ScanResumed


def test_scanresumed_garde_ses_champs() -> None:
    scan_id = UUID(int=1)
    resume_from_point_index = 3
    instance = ScanResumed(scan_id=scan_id, resume_from_point_index=resume_from_point_index)
    assert isinstance(instance, DomainEvent)
    assert instance.scan_id == scan_id
    assert instance.resume_from_point_index == resume_from_point_index


def test_scanresumed_est_immuable() -> None:
    scan_id = UUID(int=1)
    resume_from_point_index = 3
    instance = ScanResumed(scan_id=scan_id, resume_from_point_index=resume_from_point_index)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.scan_id = scan_id
