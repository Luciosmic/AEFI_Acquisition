"""At startup the ADC config goes through the single writer
(ADS131A04AdvancedConfigurator.apply_persisted_config) — the same path as the
panel's Apply — so the chip registers and the counts->V conversion always come
from the same values, and booting never rewrites ads131a04_last_config.json."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

root_dir = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root_dir / "src"))

from infrastructure.hardware.micro_controller.adapter_lifecycle_MCU import MCULifecycleAdapter
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter
from infrastructure.hardware.micro_controller.ads131a04.ads131_controller import ADS131Controller
from infrastructure.hardware.micro_controller.ads131a04.ads131a04_advanced_configurator import (
    ADS131A04AdvancedConfigurator,
)

_LAST_CONFIG_PATH = os.path.join(".aefi_acquisition", "configs", "ads131a04_last_config.json")

_CHANNELS = {str(ch): {"gain": 1, "enabled": True} for ch in range(1, 9)}


def _boot(adc_config: dict):
    """Returns ({register: value} written at boot, adapter)."""
    comm = MagicMock()
    comm.connect.return_value = True
    comm.send_command.return_value = (True, "OK")
    adapter = ADS131A04Adapter(comm)
    configurator = ADS131A04AdvancedConfigurator(adapter, ADS131Controller(comm))
    MCULifecycleAdapter(
        port="COM_TEST", communicator=comm, ads131a04_configurator=configurator
    ).initialize_all(config={"adc": adc_config})

    commands = [c.args[0] for c in comm.send_command.call_args_list]
    registers = {int(a[1:]): int(d[1:]) for a, d in zip(commands, commands[1:]) if a.startswith("a") and d.startswith("d")}
    return registers, adapter


class TestStartupAdcSingleWriter(unittest.TestCase):
    def setUp(self):
        self._last_before = open(_LAST_CONFIG_PATH).read() if os.path.exists(_LAST_CONFIG_PATH) else None

    def tearDown(self):
        last_after = open(_LAST_CONFIG_PATH).read() if os.path.exists(_LAST_CONFIG_PATH) else None
        self.assertEqual(last_after, self._last_before, "boot must not rewrite ads131a04_last_config.json")

    def test_reference_2442_writes_internal_2442(self):
        registers, adapter = _boot({"reference_voltage": 2.442, "oversampling_ratio": 4096, "channels": _CHANNELS})
        # HRM(64) + reserved(32) + INT_REFEN(8), VREF_4V=0
        self.assertEqual(registers[11], 104)
        self.assertEqual(adapter._current_config.reference_voltage, 2.442)

    def test_reference_4_sets_vref_4v_bit_and_conversion_together(self):
        registers, adapter = _boot({"reference_voltage": 4.0, "oversampling_ratio": 4096, "channels": _CHANNELS})
        self.assertEqual(registers[11], 120)
        self.assertEqual(adapter._current_config.reference_voltage, 4.0)

    def test_osr_encoded_on_clk2_bits_3_0(self):
        # ICLK_DIV=/2 (001 << 5 = 32) + OSR 128 (code 11) = 43 — datasheet CLK2 layout
        registers, _ = _boot({"reference_voltage": 2.442, "oversampling_ratio": 128, "channels": _CHANNELS})
        self.assertEqual(registers[14], 43)

    def test_physical_names_drive_a_sys_cfg_bits(self):
        registers, _ = _boot({
            "reference_voltage": 2.442, "oversampling_ratio": 4096, "channels": _CHANNELS,
            "negative_charge_pump": True, "high_resolution": False, "reference_source": "External",
        })
        # VNCPEN(128) + reserved(32), HRM=0, INT_REFEN=0
        self.assertEqual(registers[11], 160)


if __name__ == "__main__":
    unittest.main()
