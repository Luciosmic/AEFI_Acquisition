"""Caractérisation de errors : le comportement actuel, sans le changer."""
import pytest

from domain.aefi_point.errors.aefi_point_already_acquired_error import AefiPointAlreadyAcquiredError
from domain.aefi_point.errors.aefi_point_incomplete_error import AefiPointIncompleteError


def test_aefipointalreadyacquirederror_nomme_ses_arguments_dans_son_message() -> None:
    with pytest.raises(AefiPointAlreadyAcquiredError) as info:
        raise AefiPointAlreadyAcquiredError('valeur_aefi_point_id')
    assert info.value.aefi_point_id == 'valeur_aefi_point_id'
    assert "valeur_aefi_point_id" in str(info.value)


def test_aefipointincompleteerror_nomme_ses_arguments_dans_son_message() -> None:
    with pytest.raises(AefiPointIncompleteError) as info:
        raise AefiPointIncompleteError('valeur_aefi_point_id', 'valeur_expected', 'valeur_received')
    assert info.value.aefi_point_id == 'valeur_aefi_point_id'
    assert info.value.expected == 'valeur_expected'
    assert info.value.received == 'valeur_received'
    assert "valeur_aefi_point_id" in str(info.value)
