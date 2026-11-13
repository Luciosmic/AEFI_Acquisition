"""Caractérisation de scan_id : le comportement actuel, sans le changer."""
from uuid import UUID
import pytest

from domain.scan.value_objects.scan_id.scan_id import ScanId


def test_scanid_est_le_type_de_base_sous_un_autre_nom():
    valeur = UUID(int=1)
    assert ScanId(valeur) == valeur
