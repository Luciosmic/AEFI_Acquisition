import unittest
from unittest.mock import MagicMock
import sys
import os

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import helper
try:
    from tests.diagram_test_base import DiagramFriendlyTest
except ImportError:
    from diagram_test_base import DiagramFriendlyTest

from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
from interface.ui_hardware_advanced_configuration.presenter_generic_hardware_config import GenericHardwareConfigPresenter
from infrastructure.hardware.micro_controller.ads131a04.adapter_i_acquistion_port_ads131a04 import ADS131A04Adapter
from infrastructure.hardware.micro_controller.ad9106.adapter_excitation_configuration_ad9106 import AD9106Adapter

class TestE2EAdvancedConfigDiagram(DiagramFriendlyTest):
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        # 1. Mock Hardware Dependencies
        self.mock_serial = MagicMock()
        self.mock_controller = MagicMock()
        
        self.log_interaction("Test", "CREATE", "Mocks", "Created mock serial and controller")
        
        # 2. Instantiate Adapters
        self.ads131_adapter = ADS131A04Adapter(self.mock_serial)
        self.ad9106_adapter = AD9106Adapter(self.mock_controller, self.mock_serial)
        
        self.log_interaction("Test", "CREATE", "ADS131A04Adapter", "Instantiated adapter")
        self.log_interaction("Test", "CREATE", "AD9106Adapter", "Instantiated adapter")
        
        # 3. Create Service
        self.config_service = HardwareConfigurationService([
            self.ads131_adapter,
            self.ad9106_adapter
        ])
        self.log_interaction("Test", "CREATE", "HardwareConfigurationService", "Instantiated service with adapters")
        
        # 4. Create Presenter
        self.presenter = GenericHardwareConfigPresenter(self.config_service)
        self.log_interaction("Test", "CREATE", "GenericHardwareConfigPresenter", "Instantiated presenter")
        
        # 5. Connect Signals
        self.presenter.specs_loaded.connect(self._on_specs_loaded)
        self.presenter.status_message.connect(self._on_status_message)
        self.log_interaction("Test", "CONNECT", "Presenter", "Connected to specs_loaded and status_message signals")

    def _on_specs_loaded(self, hw_id, specs):
        self.log_interaction("Presenter", "SIGNAL", "Test", "specs_loaded", data={"hw_id": hw_id, "count": len(specs)})
        self.captured_specs = (hw_id, specs)

    def _on_status_message(self, msg):
        self.log_interaction("Presenter", "SIGNAL", "Test", "status_message", data={"msg": msg})
        self.captured_status.append(msg)

    def test_advanced_config_flow(self):
        self.log_divider("Execution")
        
        self.captured_specs = None
        self.captured_status = []
        
        # --- Step 1: Select Hardware (ADS131) ---
        hw_id = self.ads131_adapter.hardware_id
        self.log_interaction("Test", "CALL", "Presenter", "select_hardware", data={"hw_id": hw_id})
        
        self.presenter.select_hardware(hw_id)
        
        # Verify
        self.log_interaction("Test", "ASSERT", "Test", "Specs loaded")
        self.assertIsNotNone(self.captured_specs, "Specs should be loaded")
        self.assertEqual(self.captured_specs[0], hw_id)
        
        # --- Step 2: Apply Config (ADS131) ---
        new_config = {"reference_voltage": 3.0, "oversampling_ratio": "64"}
        self.log_interaction("Test", "CALL", "Presenter", "apply_configuration", data={"config": new_config})
        
        self.presenter.apply_configuration(new_config)
        
        # Verify
        self.log_interaction("Test", "ASSERT", "Test", "Status message received")
        self.assertTrue(any("Configuration applied" in msg for msg in self.captured_status))
        
        # --- Step 3: Select Hardware (AD9106) ---
        self.log_divider("Switch Hardware")
        hw_id_dds = self.ad9106_adapter.hardware_id
        self.log_interaction("Test", "CALL", "Presenter", "select_hardware", data={"hw_id": hw_id_dds})
        
        self.presenter.select_hardware(hw_id_dds)
        
        # --- Step 4: Apply Config (AD9106) ---
        dds_config = {"frequency_hz": 5000.0, "mode_dds1_dds2": "AC+DC"}
        self.log_interaction("Test", "CALL", "Presenter", "apply_configuration", data={"config": dds_config})
        
        self.presenter.apply_configuration(dds_config)
        
        # Verify Controller Calls
        self.log_interaction("Test", "ASSERT", "AD9106Controller", "set_dds_frequency called")
        self.mock_controller.set_dds_frequency.assert_called_with(5000.0)
        
        self.log_interaction("Test", "ASSERT", "AD9106Controller", "set_dds_channel_mode called")
        self.mock_controller.set_dds_channel_mode.assert_any_call(1, "AC")

if __name__ == '__main__':
    unittest.main()
