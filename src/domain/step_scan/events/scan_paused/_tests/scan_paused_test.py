"""Caractérisation de scan_paused : le comportement actuel, sans le changer."""
from uuid import UUID
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.step_scan.events.scan_paused.scan_paused import ScanPaused


def test_scanpaused_garde_ses_champs() -> None:
    scan_id = UUID(int=1)
    current_point_index = 3
    instance = ScanPaused(scan_id=scan_id, current_point_index=current_point_index)
    assert isinstance(instance, DomainEvent)
    assert instance.scan_id == scan_id
    assert instance.current_point_index == current_point_index


def test_scanpaused_est_immuable() -> None:
    scan_id = UUID(int=1)
    current_point_index = 3
    instance = ScanPaused(scan_id=scan_id, current_point_index=current_point_index)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.scan_id = scan_id
