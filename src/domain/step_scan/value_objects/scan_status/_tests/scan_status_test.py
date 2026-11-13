"""Caractérisation de scan_status : le comportement actuel, sans le changer."""
import pytest

from domain.step_scan.value_objects.scan_status.scan_status import ScanStatus


def test_scanstatus_liste_ses_membres():
    assert [m.name for m in ScanStatus] == ['PENDING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED']
