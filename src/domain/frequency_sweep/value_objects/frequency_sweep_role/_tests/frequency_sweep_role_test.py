"""Caractérisation de frequency_sweep_role : le comportement actuel, sans le changer."""
import pytest

from domain.frequency_sweep.value_objects.frequency_sweep_role.frequency_sweep_role import FrequencySweepRole


def test_frequencysweeprole_liste_ses_membres():
    assert [m.name for m in FrequencySweepRole] == ['INSTRUMENT_REFERENCE', 'BACKGROUND']
