"""Tests for AdapterSynchronousDetectionAD9106 — real AD9106Controller/
AD9106AdvancedConfigurator instances, serial I/O patched at the
communicator level (same fixture pattern as ad9106_advanced_configurator_test.py)."""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

root_dir = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(root_dir / "src"))

from infrastructure.hardware.micro_controller.MCU_serial_communicator import MCU_SerialCommunicator
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.ad9106.ad9106_advanced_configurator import AD9106AdvancedConfigurator
from infrastructure.hardware.micro_controller.ad9106.adapter_synchronous_detection_ad9106 import (
    AdapterSynchronousDetectionAD9106,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus

_AD9106_LAST_CONFIG_PATH = os.path.join(".aefi_acquisition", "configs", "ad9106_last_config.json")


def _backup_ad9106_last_config() -> "str | None":
    """apply_config() writes to the real relative config path — back it up so
    tests can restore it in tearDown instead of permanently corrupting the
    user's actual last-applied hardware config (mirrors
    ad9106_advanced_configurator_test.py)."""
    if os.path.exists(_AD9106_LAST_CONFIG_PATH):
        with open(_AD9106_LAST_CONFIG_PATH, "r") as f:
            return f.read()
    return None


def _restore_ad9106_last_config(backup: "str | None") -> None:
    if backup is not None:
        with open(_AD9106_LAST_CONFIG_PATH, "w") as f:
            f.write(backup)
    elif os.path.exists(_AD9106_LAST_CONFIG_PATH):
        os.remove(_AD9106_LAST_CONFIG_PATH)


class AdapterSynchronousDetectionAD9106Test(unittest.TestCase):
    def setUp(self):
        self._last_config_backup = _backup_ad9106_last_config()
        self._send_patcher = patch.object(MCU_SerialCommunicator, "send_command", return_value=(True, "OK"))
        self._send_patcher.start()
        self.controller = AD9106Controller(MCU_SerialCommunicator())
        self.event_bus = InMemoryEventBus()
        self.configurator = AD9106AdvancedConfigurator(self.controller, self.event_bus)
        self.adapter = AdapterSynchronousDetectionAD9106(self.controller, self.configurator)

    def tearDown(self):
        self._send_patcher.stop()
        _restore_ad9106_last_config(self._last_config_backup)

    def test_get_all_channel_phase_registers_reflects_state_after_apply_config(self):
        self.configurator.apply_config({"ch1_phase": 1000, "ch3_phase": 16384})

        registers = self.adapter.get_all_channel_phase_registers()

        self.assertEqual(registers[1], 1000)
        self.assertEqual(registers[3], 16384)
        # ch4 derived by quadrature enforcement (ch3 - 90deg), confirms the
        # snapshot is read live from the controller, not cached by the adapter.
        self.assertEqual(registers[4], 0)

    def test_get_all_channel_phase_registers_returns_a_copy(self):
        registers = self.adapter.get_all_channel_phase_registers()
        registers[1] = 99999

        self.assertNotEqual(self.adapter.get_all_channel_phase_registers()[1], 99999)

    def test_set_ch3_phase_register_delegates_to_configurator_apply_config(self):
        with patch.object(self.configurator, "apply_config") as mock_apply_config:
            self.adapter.set_ch3_phase_register(12345)

        mock_apply_config.assert_called_once_with({"ch3_phase": 12345}, persist=False)

    def test_set_ch3_phase_register_actually_writes_the_register(self):
        self.adapter.set_ch3_phase_register(20000)

        self.assertEqual(self.adapter.get_all_channel_phase_registers()[3], 20000)

    def test_set_ch3_phase_register_does_not_persist_to_last_config(self):
        # Establish a manual baseline first (persisted, as a real user edit
        # via Hardware Advanced Config would be).
        self.configurator.apply_config({"ch3_phase": 5000})
        with open(_AD9106_LAST_CONFIG_PATH, "r") as f:
            persisted_after_manual_edit = json.load(f)
        self.assertEqual(persisted_after_manual_edit["channels"]["3"]["phase"], 5000)

        # A compensation-driven write must NOT overwrite that manual baseline.
        self.adapter.set_ch3_phase_register(20000)

        self.assertEqual(self.adapter.get_all_channel_phase_registers()[3], 20000)  # live register moved
        with open(_AD9106_LAST_CONFIG_PATH, "r") as f:
            persisted_after_compensation = json.load(f)
        self.assertEqual(persisted_after_compensation["channels"]["3"]["phase"], 5000)  # file unchanged

    def test_restore_manual_configuration_delegates_to_configurator_reload_last_config(self):
        with patch.object(self.configurator, "reload_last_config") as mock_reload:
            self.adapter.restore_manual_configuration()

        mock_reload.assert_called_once_with()

    def test_is_quadrature_enforcement_enabled_reflects_configurator_default(self):
        self.assertTrue(self.adapter.is_quadrature_enforcement_enabled())

    def test_is_quadrature_enforcement_enabled_reflects_configurator_after_disabling(self):
        self.configurator.apply_config({"enforce_dds3_dds4_quadrature": False})

        self.assertFalse(self.adapter.is_quadrature_enforcement_enabled())


if __name__ == "__main__":
    unittest.main()
