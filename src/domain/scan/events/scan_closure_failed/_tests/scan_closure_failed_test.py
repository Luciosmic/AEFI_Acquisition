"""Caractérisation de scan_closure_failed : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.scan.events.scan_closure_failed.scan_closure_failed import ScanClosureFailed
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_scanclosurefailed_garde_ses_champs() -> None:
    scan_id = UUID(int=1)
    source = "x"
    acquisition_id = UUID(int=1)
    reason = "x"
    instance = ScanClosureFailed(scan_id=scan_id, source=source, acquisition_id=acquisition_id, reason=reason)
    assert isinstance(instance, DomainEvent)
    assert instance.scan_id == scan_id
    assert instance.source == source
    assert instance.acquisition_id == acquisition_id
    assert instance.reason == reason


def test_scanclosurefailed_est_immuable() -> None:
    scan_id = UUID(int=1)
    source = "x"
    acquisition_id = UUID(int=1)
    reason = "x"
    instance = ScanClosureFailed(scan_id=scan_id, source=source, acquisition_id=acquisition_id, reason=reason)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.scan_id = scan_id
