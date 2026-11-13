"""Caractérisation de scan_pattern : le comportement actuel, sans le changer."""
import pytest

from domain.step_scan.value_objects.scan_pattern.scan_pattern import ScanPattern


def test_scanpattern_liste_ses_membres():
    assert [m.name for m in ScanPattern] == ['SERPENTINE', 'RASTER', 'COMB']
