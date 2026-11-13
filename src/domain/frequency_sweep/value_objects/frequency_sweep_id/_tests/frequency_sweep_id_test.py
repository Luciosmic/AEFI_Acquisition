"""Caractérisation de frequency_sweep_id : le comportement actuel, sans le changer."""
from uuid import UUID
import pytest

from domain.frequency_sweep.value_objects.frequency_sweep_id.frequency_sweep_id import FrequencySweepId


def test_frequencysweepid_est_le_type_de_base_sous_un_autre_nom() -> None:
    valeur = UUID(int=1)
    assert FrequencySweepId(valeur) == valeur
