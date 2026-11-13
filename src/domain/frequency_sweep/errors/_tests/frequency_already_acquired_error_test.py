"""Caractérisation de errors : le comportement actuel, sans le changer."""
import pytest

from domain.frequency_sweep.errors.frequency_already_acquired_error import FrequencyAlreadyAcquiredError
from domain.frequency_sweep.errors.frequency_not_in_grid_error import FrequencyNotInGridError
from domain.frequency_sweep.errors.frequency_point_incomplete_error import FrequencyPointIncompleteError


def test_frequencyalreadyacquirederror_nomme_ses_arguments_dans_son_message() -> None:
    with pytest.raises(FrequencyAlreadyAcquiredError) as info:
        raise FrequencyAlreadyAcquiredError('valeur_frequency_sweep_id', 'valeur_frequency_hz')
    assert info.value.frequency_sweep_id == 'valeur_frequency_sweep_id'
    assert info.value.frequency_hz == 'valeur_frequency_hz'
    assert "valeur_frequency_sweep_id" in str(info.value)


def test_frequencynotingriderror_nomme_ses_arguments_dans_son_message() -> None:
    with pytest.raises(FrequencyNotInGridError) as info:
        raise FrequencyNotInGridError('valeur_frequency_sweep_id', 'valeur_frequency_hz')
    assert info.value.frequency_sweep_id == 'valeur_frequency_sweep_id'
    assert info.value.frequency_hz == 'valeur_frequency_hz'
    assert "valeur_frequency_sweep_id" in str(info.value)


def test_frequencypointincompleteerror_nomme_ses_arguments_dans_son_message() -> None:
    with pytest.raises(FrequencyPointIncompleteError) as info:
        raise FrequencyPointIncompleteError('valeur_frequency_sweep_id', 'valeur_frequency_hz', 'valeur_expected', 'valeur_received')
    assert info.value.frequency_sweep_id == 'valeur_frequency_sweep_id'
    assert info.value.frequency_hz == 'valeur_frequency_hz'
    assert info.value.expected == 'valeur_expected'
    assert info.value.received == 'valeur_received'
    assert "valeur_frequency_sweep_id" in str(info.value)
