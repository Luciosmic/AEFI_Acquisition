"""Caractérisation de scan_failed : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.step_scan.events.scan_failed.scan_failed import ScanFailed


def test_scanfailed_garde_ses_champs() -> None:
    scan_id = UUID(int=1)
    reason = "x"
    instance = ScanFailed(scan_id=scan_id, reason=reason)
    assert isinstance(instance, DomainEvent)
    assert instance.scan_id == scan_id
    assert instance.reason == reason


def test_scanfailed_est_immuable() -> None:
    scan_id = UUID(int=1)
    reason = "x"
    instance = ScanFailed(scan_id=scan_id, reason=reason)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.scan_id = scan_id  # type: ignore[misc]
