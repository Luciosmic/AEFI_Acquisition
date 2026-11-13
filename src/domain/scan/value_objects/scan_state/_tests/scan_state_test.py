"""Caractérisation de scan_state : le comportement actuel, sans le changer."""
import pytest

from domain.scan.value_objects.scan_state.scan_state import ScanState


def test_scanstate_liste_ses_membres():
    assert [m.name for m in ScanState] == ['PENDING', 'STARTED', 'COMPLETED']
