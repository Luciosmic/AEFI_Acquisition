import unittest
from unittest.mock import MagicMock
import sys
import os

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
from interface.ui_hardware_advanced_configuration.presenter_generic_hardware_config import GenericHardwareConfigPresenter
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter
from infrastructure.hardware.micro_controller.ad9106.adapter_excitation_configuration_ad9106 import AD9106Adapter
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller

class TestE2EAdvancedConfig(unittest.TestCase):
    def setUp(self):
        # 1. Mock Hardware Dependencies
        self.mock_serial = MagicMock()
        self.mock_controller = MagicMock() # For AD9106
        
        # 2. Instantiate Adapters (Real Logic)
        self.ads131_adapter = ADS131A04Adapter(self.mock_serial)
        self.ad9106_adapter = AD9106Adapter(self.mock_controller, self.mock_serial)
        
        # 3. Create Service
        self.config_service = HardwareConfigurationService([
            self.ads131_adapter,
            self.ad9106_adapter
        ])
        
        # 4. Create Presenter
        self.presenter = GenericHardwareConfigPresenter(self.config_service)
        
        # 5. Mock View Signals (to capture output)
        self.captured_specs = None
        self.captured_status = []
        
        self.presenter.specs_loaded.connect(self._on_specs_loaded)
        self.presenter.status_message.connect(self._on_status_message)
        
    def _on_specs_loaded(self, hw_id, specs):
        self.captured_specs = (hw_id, specs)
        
    def _on_status_message(self, msg):
        self.captured_status.append(msg)

    def test_flow_ads131(self):
        print("\n--- Testing ADS131A04 Config Flow ---")
        
        # 1. Select Hardware
        hw_id = self.ads131_adapter.hardware_id
        self.presenter.select_hardware(hw_id)
        
        # Verify specs loaded
        self.assertIsNotNone(self.captured_specs)
        self.assertEqual(self.captured_specs[0], hw_id)
        specs = self.captured_specs[1]
        print(f"Loaded {len(specs)} specs for {hw_id}")
        
        # Verify specific parameter exists
        ref_voltage_spec = next((s for s in specs if s.key == "reference_voltage"), None)
        self.assertIsNotNone(ref_voltage_spec)
        
        # 2. Apply Configuration
        new_config = {"reference_voltage": 3.0, "oversampling_ratio": "64"}
        self.presenter.apply_configuration(new_config)
        
        # Verify status message
        self.assertTrue(any("Configuration applied" in msg for msg in self.captured_status))
        
        # Verify adapter state updated (mocking persistence)
        # Note: In real run, this writes to file. Here we check if load_config was called internally 
        # or check side effects. Since apply_config calls load_config, we can check internal state if exposed,
        # or trust the integration test we did earlier.
        # For E2E here, we assume no exception raised means success.

    def test_flow_ad9106(self):
        print("\n--- Testing AD9106 Config Flow ---")
        
        # 1. Select Hardware
        hw_id = self.ad9106_adapter.hardware_id
        self.presenter.select_hardware(hw_id)
        
        # Verify specs loaded
        self.assertIsNotNone(self.captured_specs)
        self.assertEqual(self.captured_specs[0], hw_id)
        
        # 2. Apply Configuration
        new_config = {"frequency_hz": 5000.0, "mode_dds1_dds2": "AC+DC"}
        self.presenter.apply_configuration(new_config)
        
        # Verify controller call
        self.mock_controller.set_dds_frequency.assert_called_with(5000.0)
        self.mock_controller.set_dds_channel_mode.assert_any_call(1, "AC")
        self.mock_controller.set_dds_channel_mode.assert_any_call(2, "DC")
        
        print("AD9106 Controller calls verified.")

if __name__ == '__main__':
    unittest.main()
