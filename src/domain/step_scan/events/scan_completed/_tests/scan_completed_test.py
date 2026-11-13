"""Caractérisation de scan_completed : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted


def test_scancompleted_garde_ses_champs():
    scan_id = UUID(int=1)
    total_points = 3
    instance = ScanCompleted(scan_id=scan_id, total_points=total_points)
    assert isinstance(instance, DomainEvent)
    assert instance.scan_id == scan_id
    assert instance.total_points == total_points


def test_scancompleted_est_immuable():
    scan_id = UUID(int=1)
    total_points = 3
    instance = ScanCompleted(scan_id=scan_id, total_points=total_points)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.scan_id = scan_id
