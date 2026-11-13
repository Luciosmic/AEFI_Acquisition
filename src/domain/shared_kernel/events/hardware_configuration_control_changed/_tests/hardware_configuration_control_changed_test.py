"""Caractérisation de hardware_configuration_control_changed : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.hardware_configuration_control_changed.hardware_configuration_control_changed import HardwareConfigurationControlChanged


def test_hardwareconfigurationcontrolchanged_garde_ses_champs() -> None:
    hardware_id = "x"
    controller = None
    instance = HardwareConfigurationControlChanged(hardware_id=hardware_id, controller=controller)
    assert isinstance(instance, DomainEvent)
    assert instance.hardware_id == hardware_id
    assert instance.controller == controller


def test_hardwareconfigurationcontrolchanged_est_immuable() -> None:
    hardware_id = "x"
    controller = None
    instance = HardwareConfigurationControlChanged(hardware_id=hardware_id, controller=controller)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.hardware_id = hardware_id  # type: ignore[misc]
