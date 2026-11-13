"""Caractérisation de scan_cancelled : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.step_scan.events.scan_cancelled.scan_cancelled import ScanCancelled


def test_scancancelled_garde_ses_champs() -> None:
    scan_id = UUID(int=1)
    instance = ScanCancelled(scan_id=scan_id)
    assert isinstance(instance, DomainEvent)
    assert instance.scan_id == scan_id


def test_scancancelled_est_immuable() -> None:
    scan_id = UUID(int=1)
    instance = ScanCancelled(scan_id=scan_id)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.scan_id = scan_id  # type: ignore[misc]
