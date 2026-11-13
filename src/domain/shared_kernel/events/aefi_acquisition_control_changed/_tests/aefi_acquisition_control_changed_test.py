"""Caractérisation de aefi_acquisition_control_changed : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.aefi_acquisition_control_changed.aefi_acquisition_control_changed import AefiAcquisitionControlChanged
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def test_aefiacquisitioncontrolchanged_garde_ses_champs() -> None:
    controller = None
    instance = AefiAcquisitionControlChanged(controller=controller)
    assert isinstance(instance, DomainEvent)
    assert instance.controller == controller


def test_aefiacquisitioncontrolchanged_est_immuable() -> None:
    controller = None
    instance = AefiAcquisitionControlChanged(controller=controller)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.controller = controller
