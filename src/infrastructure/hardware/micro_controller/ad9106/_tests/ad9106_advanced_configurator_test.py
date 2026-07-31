"""Tests for AD9106AdvancedConfigurator's ExcitationFrequencyChanged publication."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

root_dir = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(root_dir / "src"))

from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.ad9106.ad9106_advanced_configurator import AD9106AdvancedConfigurator
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from domain.shared_kernel.excitation.events.excitation_frequency_changed.excitation_frequency_changed import (
    ExcitationFrequencyChanged,
)
from domain.shared_kernel.excitation.events.dds_channel_config_changed.dds_channel_config_changed import (
    DdsChannelConfigChanged,
)


class TestAD9106AdvancedConfiguratorFrequencyEvent(unittest.TestCase):
    def setUp(self):
        self._send_patcher = patch.object(MCU_SerialCommunicator, 'send_command', return_value=(True, "OK"))
        self._send_patcher.start()
        self.controller = AD9106Controller(MCU_SerialCommunicator())
        self.event_bus = InMemoryEventBus()
        self.events = []
        self.event_bus.subscribe("excitationfrequencychanged", self.events.append)
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)

    def tearDown(self):
        self._send_patcher.stop()

    def test_apply_config_publishes_event_when_frequency_changes(self):
        self.configurator.apply_config({"frequency_hz": 2000.0})

        self.assertEqual(len(self.events), 1)
        self.assertIsInstance(self.events[0], ExcitationFrequencyChanged)
        self.assertEqual(self.events[0].frequency_hz, 2000.0)

    def test_apply_config_does_not_republish_when_frequency_unchanged(self):
        self.configurator.apply_config({"frequency_hz": 2000.0})
        self.configurator.apply_config({"frequency_hz": 2000.0, "ch1_gain": 100.0})

        self.assertEqual(len(self.events), 1)

    def test_apply_config_without_frequency_key_does_not_publish(self):
        self.configurator.apply_config({"ch1_gain": 100.0})

        self.assertEqual(len(self.events), 0)


class TestAD9106AdvancedConfiguratorChannelEvent(unittest.TestCase):
    """ExcitationConfigurationService listens for this to recompute level and
    detect a non-standard phase pair (-> CUSTOM mode) when the Hardware
    Config tab edits channel 1/2 gain/phase directly."""

    def setUp(self):
        self._send_patcher = patch.object(MCU_SerialCommunicator, 'send_command', return_value=(True, "OK"))
        self._send_patcher.start()
        self.controller = AD9106Controller(MCU_SerialCommunicator())
        self.event_bus = InMemoryEventBus()
        self.events = []
        self.event_bus.subscribe("ddschannelconfigchanged", self.events.append)
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)

    def tearDown(self):
        self._send_patcher.stop()

    def test_apply_config_publishes_event_for_changed_channel_1_and_2(self):
        self.configurator.apply_config({"ch1_gain": 1000, "ch1_phase": 0, "ch2_gain": 2000, "ch2_phase": 16000})

        self.assertEqual({e.channel for e in self.events}, {1, 2})
        by_channel = {e.channel: e for e in self.events}
        self.assertEqual(by_channel[1].gain, 1000)
        self.assertEqual(by_channel[1].phase, 0)
        self.assertEqual(by_channel[2].gain, 2000)
        self.assertEqual(by_channel[2].phase, 16000)

    def test_apply_config_does_not_publish_for_channels_3_and_4(self):
        self.configurator.apply_config({"ch3_gain": 5000, "ch4_phase": 100})

        self.assertEqual(self.events, [])

    def test_apply_config_does_not_republish_unchanged_channel(self):
        self.configurator.apply_config({"ch1_gain": 1000, "ch1_phase": 0})
        self.configurator.apply_config({"ch1_gain": 1000, "ch1_phase": 0})

        self.assertEqual(len(self.events), 1)

    def test_apply_config_republishes_when_only_phase_changes(self):
        self.configurator.apply_config({"ch1_gain": 1000, "ch1_phase": 0})
        self.configurator.apply_config({"ch1_gain": 1000, "ch1_phase": 16000})

        self.assertEqual(len(self.events), 2)
        self.assertEqual(self.events[-1].phase, 16000)


if __name__ == "__main__":
    unittest.main()
