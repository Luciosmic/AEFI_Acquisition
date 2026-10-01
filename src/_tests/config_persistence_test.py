import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

import unittest
import json
import shutil
from unittest.mock import MagicMock

from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter
from infrastructure.hardware.micro_controller.ads131a04.ads131a04_advanced_configurator import ADS131A04AdvancedConfigurator

class TestConfigPersistence(unittest.TestCase):
    def setUp(self):
        # Paths — configs live in .aefi_acquisition/configs/ (seeded from config_templates/)
        self.default_config_path = os.path.join(".aefi_acquisition", "configs", "ads131a04_default_config.json")
        self.last_config_path = os.path.join(".aefi_acquisition", "configs", "ads131a04_last_config.json")
        
        # Backup existing files to restore later
        self.backup_last_config = None
        if os.path.exists(self.last_config_path):
            with open(self.last_config_path, 'r') as f:
                self.backup_last_config = f.read()
        
        # Read default config content for verification
        with open(self.default_config_path, 'r') as f:
            self.original_default_content = f.read()

        # Mock Adapter
        self.mock_serial = MagicMock()
        self.adapter = ADS131A04Adapter(self.mock_serial)
        self.mock_controller = MagicMock()
        for writer in ("set_clkin_divider", "set_iclk_divider_and_oversampling", "set_reference_config", "set_channel_gain"):
            getattr(self.mock_controller, writer).return_value = (True, "OK")
        self.configurator = ADS131A04AdvancedConfigurator(self.adapter, self.mock_controller)

    def tearDown(self):
        # Restore last config
        if self.backup_last_config:
            with open(self.last_config_path, 'w') as f:
                f.write(self.backup_last_config)
        elif os.path.exists(self.last_config_path):
            os.remove(self.last_config_path)

    def test_apply_config_updates_last_config_only(self):
        """Verify that applying config updates last_config.json but NOT default_config.json"""

        # 1. Use a config with a distinctive oversampling_ratio that differs from the default
        #    — it is preserved verbatim in the saved JSON.
        new_config = {
            "oversampling_ratio": 128,  # Changed from default (4096)
            "gain_pair_1": 1,
            "gain_pair_2": 1,
            "gain_pair_3": 1,
            "gain_pair_4": 1,
        }

        # 2. Apply configuration
        self.configurator.apply_config(new_config)

        # 3. Verify last_config.json is created and contains the changed value
        self.assertTrue(os.path.exists(self.last_config_path), "last_config.json should exist")
        with open(self.last_config_path, 'r') as f:
            saved_config = json.load(f)

        self.assertEqual(saved_config["oversampling_ratio"], 128)

        # 4. Verify default_config.json is UNCHANGED
        with open(self.default_config_path, 'r') as f:
            current_default_content = f.read()

        self.assertEqual(self.original_default_content, current_default_content,
                         "default_config.json should NOT be modified")

        print("\n[Test] Persistence verified: last_config updated, default_config untouched.")

    def test_apply_4v_reference_reaches_chip_and_conversion_together(self):
        """One name (reference_voltage, volts) drives both the chip register and the counts->V math."""
        self.configurator.apply_config({"reference_voltage": "4.0V"})

        self.assertEqual(self.mock_controller.set_reference_config.call_args.kwargs["reference_voltage"], 4.0)
        self.assertEqual(self.adapter._current_config.reference_voltage, 4.0)
        with open(self.last_config_path, 'r') as f:
            saved = json.load(f)
        self.assertEqual(saved["reference_voltage"], 4.0)

    def test_saved_config_uses_one_physical_name_per_setting(self):
        self.configurator.apply_config({"negative_charge_pump": True, "high_resolution": False, "reference_source": "External"})

        with open(self.last_config_path, 'r') as f:
            saved = json.load(f)
        self.assertEqual(
            (saved["negative_charge_pump"], saved["high_resolution"], saved["reference_source"]),
            (True, False, "External"),
        )
        for legacy in ("ref_voltage", "vncpen", "negative_ref", "high_res", "resolution_mode", "ref_selection"):
            self.assertNotIn(legacy, saved)

    def test_apply_writes_oversampling_ratio_to_chip(self):
        self.configurator.apply_config({"oversampling_ratio": "128"})

        self.mock_controller.set_iclk_divider_and_oversampling.assert_called_once_with(2, 128)

if __name__ == '__main__':
    unittest.main()
