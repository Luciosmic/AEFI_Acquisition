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
        # Paths
        self.base_dir = os.path.join(os.path.dirname(__file__), "../infrastructure/hardware/micro_controller/ads131a04")
        self.default_config_path = os.path.join(self.base_dir, "ads131a04_default_config.json")
        self.last_config_path = os.path.join(self.base_dir, "ads131a04_last_config.json")
        
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
        self.mock_controller.set_channel_gain.return_value = (True, "OK")
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

        # 1. Use a config with a distinctive oversampling_ratio that differs from the default.
        #    apply_config() maps 'reference_voltage' to a register int ('ref_voltage'), so
        #    we verify 'oversampling_ratio' instead — it is preserved verbatim in the saved JSON.
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

if __name__ == '__main__':
    unittest.main()
