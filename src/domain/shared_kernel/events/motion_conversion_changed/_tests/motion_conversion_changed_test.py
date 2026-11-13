"""Caractérisation de motion_conversion_changed : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.motion_conversion_changed.motion_conversion_changed import MotionConversionChanged


def test_motionconversionchanged_garde_ses_champs() -> None:
    previous_microns_per_pulse = None
    microns_per_pulse = 1.5
    motor_name = "x"
    stepper_driver_name = "x"
    instance = MotionConversionChanged(previous_microns_per_pulse=previous_microns_per_pulse, microns_per_pulse=microns_per_pulse, motor_name=motor_name, stepper_driver_name=stepper_driver_name)
    assert isinstance(instance, DomainEvent)
    assert instance.previous_microns_per_pulse == previous_microns_per_pulse
    assert instance.microns_per_pulse == microns_per_pulse
    assert instance.motor_name == motor_name
    assert instance.stepper_driver_name == stepper_driver_name


def test_motionconversionchanged_est_immuable() -> None:
    previous_microns_per_pulse = None
    microns_per_pulse = 1.5
    motor_name = "x"
    stepper_driver_name = "x"
    instance = MotionConversionChanged(previous_microns_per_pulse=previous_microns_per_pulse, microns_per_pulse=microns_per_pulse, motor_name=motor_name, stepper_driver_name=stepper_driver_name)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.previous_microns_per_pulse = previous_microns_per_pulse
