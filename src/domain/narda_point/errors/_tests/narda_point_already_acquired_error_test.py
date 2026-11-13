"""Caractérisation de errors : le comportement actuel, sans le changer."""
import pytest

from domain.narda_point.errors.narda_point_already_acquired_error import NardaPointAlreadyAcquiredError
from domain.narda_point.errors.narda_point_incomplete_error import NardaPointIncompleteError


def test_nardapointalreadyacquirederror_nomme_ses_arguments_dans_son_message() -> None:
    with pytest.raises(NardaPointAlreadyAcquiredError) as info:
        raise NardaPointAlreadyAcquiredError('valeur_narda_point_id')
    assert info.value.narda_point_id == 'valeur_narda_point_id'
    assert "valeur_narda_point_id" in str(info.value)


def test_nardapointincompleteerror_nomme_ses_arguments_dans_son_message() -> None:
    with pytest.raises(NardaPointIncompleteError) as info:
        raise NardaPointIncompleteError('valeur_narda_point_id', 'valeur_expected', 'valeur_received')  # type: ignore[arg-type]
    assert info.value.narda_point_id == 'valeur_narda_point_id'
    assert info.value.expected == 'valeur_expected'
    assert info.value.received == 'valeur_received'
    assert "valeur_narda_point_id" in str(info.value)
