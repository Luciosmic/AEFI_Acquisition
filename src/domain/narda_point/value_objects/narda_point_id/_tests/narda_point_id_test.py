"""Caractérisation de narda_point_id : le comportement actuel, sans le changer."""
from uuid import UUID
import pytest

from domain.narda_point.value_objects.narda_point_id.narda_point_id import NardaPointId


def test_nardapointid_est_le_type_de_base_sous_un_autre_nom():
    valeur = UUID(int=1)
    assert NardaPointId(valeur) == valeur
