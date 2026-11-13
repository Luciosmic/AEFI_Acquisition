"""Caractérisation de hardware_configuration : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import BooleanParameterSchema
from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import EnumParameterSchema
from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import HardwareAdvancedParameterSchema
from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import NumberParameterSchema
from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import ParameterType


def test_parametertype_liste_ses_membres():
    assert [m.name for m in ParameterType] == ['NUMBER', 'ENUM', 'BOOLEAN']


def test_hardwareadvancedparameterschema_garde_ses_champs():
    key = "x"
    display_name = "x"
    instance = HardwareAdvancedParameterSchema(key=key, display_name=display_name)
    assert instance.key == key
    assert instance.display_name == display_name


def test_hardwareadvancedparameterschema_est_immuable():
    key = "x"
    display_name = "x"
    instance = HardwareAdvancedParameterSchema(key=key, display_name=display_name)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.key = key


def test_numberparameterschema_garde_ses_champs():
    key = "x"
    display_name = "x"
    instance = NumberParameterSchema(key=key, display_name=display_name)
    assert instance.key == key
    assert instance.display_name == display_name


def test_numberparameterschema_est_immuable():
    key = "x"
    display_name = "x"
    instance = NumberParameterSchema(key=key, display_name=display_name)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.key = key


def test_enumparameterschema_garde_ses_champs():
    key = "x"
    display_name = "x"
    instance = EnumParameterSchema(key=key, display_name=display_name)
    assert instance.key == key
    assert instance.display_name == display_name


def test_enumparameterschema_est_immuable():
    key = "x"
    display_name = "x"
    instance = EnumParameterSchema(key=key, display_name=display_name)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.key = key


def test_booleanparameterschema_garde_ses_champs():
    key = "x"
    display_name = "x"
    instance = BooleanParameterSchema(key=key, display_name=display_name)
    assert instance.key == key
    assert instance.display_name == display_name


def test_booleanparameterschema_est_immuable():
    key = "x"
    display_name = "x"
    instance = BooleanParameterSchema(key=key, display_name=display_name)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.key = key
