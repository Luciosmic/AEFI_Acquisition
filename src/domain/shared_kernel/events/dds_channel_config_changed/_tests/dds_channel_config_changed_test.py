"""Caractérisation de dds_channel_config_changed : le comportement actuel, sans le changer."""
import dataclasses
import pytest

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from domain.shared_kernel.events.dds_channel_config_changed.dds_channel_config_changed import DdsChannelConfigChanged


def test_ddschannelconfigchanged_garde_ses_champs() -> None:
    channel = 3
    gain = 3
    phase = 3
    instance = DdsChannelConfigChanged(channel=channel, gain=gain, phase=phase)
    assert isinstance(instance, DomainEvent)
    assert instance.channel == channel
    assert instance.gain == gain
    assert instance.phase == phase


def test_ddschannelconfigchanged_est_immuable() -> None:
    channel = 3
    gain = 3
    phase = 3
    instance = DdsChannelConfigChanged(channel=channel, gain=gain, phase=phase)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.channel = channel  # type: ignore[misc]
