"""Caractérisation de errors : le comportement actuel, sans le changer."""
import pytest

from domain.measured_object_registry.errors.measured_object_name_blank_error import MeasuredObjectNameBlankError


def test_measuredobjectnameblankerror_est_une_exception_qui_garde_son_message():
    with pytest.raises(MeasuredObjectNameBlankError) as info:
        raise MeasuredObjectNameBlankError("raison")
    assert "raison" in str(info.value)
