"""Caractérisation de errors : le comportement actuel, sans le changer."""
import pytest

from domain.operator_registry.errors.operator_name_blank_error import OperatorNameBlankError


def test_operatornameblankerror_est_une_exception_qui_garde_son_message():
    with pytest.raises(OperatorNameBlankError) as info:
        raise OperatorNameBlankError("raison")
    assert "raison" in str(info.value)
