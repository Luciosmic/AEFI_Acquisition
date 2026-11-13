"""Caractérisation de scan_axis : le comportement actuel, sans le changer."""
import pytest

from domain.step_scan.value_objects.scan_axis.scan_axis import ScanAxis


def test_scanaxis_liste_ses_membres() -> None:
    assert [m.name for m in ScanAxis] == ['Y', 'X']
