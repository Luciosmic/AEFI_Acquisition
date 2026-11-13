"""Caractérisation de aefi_point_id : le comportement actuel, sans le changer."""
from uuid import UUID
import pytest

from domain.aefi_point.value_objects.aefi_point_id.aefi_point_id import AefiPointId


def test_aefipointid_est_le_type_de_base_sous_un_autre_nom() -> None:
    valeur = UUID(int=1)
    assert AefiPointId(valeur) == valeur
