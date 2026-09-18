"""Tests for MCULifecycleAdapter's JSON-driven DDS config path at startup.

Before this, `initialize_all(config={"dds": {...}})` was never exercised by
any test — only the no-config legacy fallback (_init_default_hardware_config)
was covered. That gap is exactly why the frequency/gain-not-applied bug
shipped unnoticed: nothing asserted that a startup config dict actually
reached the hardware or the domain event bus.
"""

import os
import sys
import unittest
from pathlib import Path

root_dir = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root_dir / "src"))

from infrastructure.hardware.micro_controller.fake.fake_mcu_serial_communicator import (
    FakeMCUSerialCommunicator,
)
from infrastructure.hardware.micro_controller.adapter_lifecycle_MCU import MCULifecycleAdapter
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.ad9106.ad9106_advanced_configurator import AD9106AdvancedConfigurator
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from domain.shared_kernel.excitation.events.excitation_frequency_changed.excitation_frequency_changed import (
    ExcitationFrequencyChanged,
)
from domain.shared_kernel.excitation.events.dds_channel_config_changed.dds_channel_config_changed import (
    DdsChannelConfigChanged,
)


DDS_CONFIG = {
    "frequency_hz": 10000.0,
    "channels": {
        "1": {"gain": 0, "phase": 0, "offset": 0},
        "2": {"gain": 0, "phase": 32768, "offset": 0},
        "3": {"gain": 10000, "phase": 16384, "offset": 0},
        "4": {"gain": 10000, "phase": 0, "offset": 0},
    },
}


_AD9106_LAST_CONFIG_PATH = os.path.join(".aefi_acquisition", "configs", "ad9106_last_config.json")


class TestMCULifecycleAdapterDdsConfigDelegation(unittest.TestCase):
    def setUp(self):
        # apply_config() (called via delegation below) writes to the real
        # relative config path — back it up/restore it so this test doesn't
        # corrupt the user's actual last-applied hardware config.
        if os.path.exists(_AD9106_LAST_CONFIG_PATH):
            with open(_AD9106_LAST_CONFIG_PATH, "r") as f:
                self._last_config_backup = f.read()
        else:
            self._last_config_backup = None

        self.comm = FakeMCUSerialCommunicator()
        self.controller = AD9106Controller(self.comm)
        self.event_bus = InMemoryEventBus()
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)
        self.lifecycle = MCULifecycleAdapter(
            port="COM_TEST",
            communicator=self.comm,
            ad9106_configurator=self.configurator,
        )

    def tearDown(self):
        if self._last_config_backup is not None:
            with open(_AD9106_LAST_CONFIG_PATH, "w") as f:
                f.write(self._last_config_backup)
        elif os.path.exists(_AD9106_LAST_CONFIG_PATH):
            os.remove(_AD9106_LAST_CONFIG_PATH)

    def test_startup_applies_frequency_to_hardware(self):
        self.lifecycle.initialize_all(config={"dds": DDS_CONFIG})

        self.assertEqual(self.controller.get_memory_state()["DDS"]["Frequence"], 10000.0)

    def test_startup_applies_channel_3_and_4_gain(self):
        self.lifecycle.initialize_all(config={"dds": DDS_CONFIG})

        gains = self.controller.get_memory_state()["DDS"]["Gain"]
        self.assertEqual(gains[3], 10000)
        self.assertEqual(gains[4], 10000)

    def test_startup_publishes_excitation_frequency_changed(self):
        events = []
        self.event_bus.subscribe("excitationfrequencychanged", events.append)

        self.lifecycle.initialize_all(config={"dds": DDS_CONFIG})

        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], ExcitationFrequencyChanged)
        self.assertEqual(events[0].frequency_hz, 10000.0)

    def test_startup_publishes_dds_channel_config_changed_for_channels_1_and_2(self):
        events = []
        self.event_bus.subscribe("ddschannelconfigchanged", events.append)

        self.lifecycle.initialize_all(config={"dds": DDS_CONFIG})

        self.assertEqual({e.channel for e in events}, {1, 2})
        by_channel = {e.channel: e for e in events}
        self.assertIsInstance(by_channel[2], DdsChannelConfigChanged)
        self.assertEqual(by_channel[2].phase, 32768)

    def test_without_injected_configurator_startup_does_not_crash(self):
        lifecycle = MCULifecycleAdapter(port="COM_TEST", communicator=FakeMCUSerialCommunicator())

        lifecycle.initialize_all(config={"dds": DDS_CONFIG})  # should warn, not raise


if __name__ == "__main__":
    unittest.main()
