"""Caractérisation de motion_conversion_found_missing : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.motion_conversion_found_missing.motion_conversion_found_missing import MotionConversionFoundMissing


def test_motionconversionfoundmissing_garde_ses_champs() -> None:
    motor_name = None
    missing_quantity = "x"
    where_to_enter = "x"
    instance = MotionConversionFoundMissing(motor_name=motor_name, missing_quantity=missing_quantity, where_to_enter=where_to_enter)
    assert isinstance(instance, DomainEvent)
    assert instance.motor_name == motor_name
    assert instance.missing_quantity == missing_quantity
    assert instance.where_to_enter == where_to_enter


def test_motionconversionfoundmissing_est_immuable() -> None:
    motor_name = None
    missing_quantity = "x"
    where_to_enter = "x"
    instance = MotionConversionFoundMissing(motor_name=motor_name, missing_quantity=missing_quantity, where_to_enter=where_to_enter)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.motor_name = motor_name  # type: ignore[misc]
