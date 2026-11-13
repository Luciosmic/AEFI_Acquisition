"""Caractérisation de aefi_line_id : le comportement actuel, sans le changer."""
from uuid import UUID
import pytest

from domain.aefi_line.value_objects.aefi_line_id.aefi_line_id import AefiLineId


def test_aefilineid_est_le_type_de_base_sous_un_autre_nom() -> None:
    valeur = UUID(int=1)
    assert AefiLineId(valeur) == valeur
