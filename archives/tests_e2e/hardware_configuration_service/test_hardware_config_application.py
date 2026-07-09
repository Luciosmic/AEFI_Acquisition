"""
E2E Test: Hardware Configuration Application

Tests applying hardware configuration through HardwareConfigurationService.
Validates: apply config → config routed → hardware updated.
"""

import unittest
from tests_e2e.base import DiagramFriendlyTest
from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
# Note: FakeHardwareConfigProvider has import issue, using inline mock
from typing import Dict, Any
from application.services.hardware_configuration_service.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator

class SimpleFakeHardwareConfigProvider(IHardwareAdvancedConfigurator):
    def __init__(self, hardware_id: str):
        self._hardware_id = hardware_id
        self.applied_config: Dict[str, Any] = {}
        self.applied_hs = None
        self.saved_default_config: Dict[str, Any] = {}
    
    @property
    def hardware_id(self) -> str:
        return self._hardware_id
    
    @property
    def display_name(self) -> str:
        return f"Mock Hardware ({self._hardware_id})"
    
    @staticmethod
    def get_parameter_specs():
        return []
    
    def apply_config(self, config: Dict[str, Any]) -> None:
        self.applied_config.update(config)
        if 'hs' in config:
            self.applied_hs = config['hs']
    
    def save_config_as_default(self, config: Dict[str, Any]) -> None:
        self.saved_default_config.update(config)

FakeHardwareConfigProvider = SimpleFakeHardwareConfigProvider


class TestHardwareConfigApplication(DiagramFriendlyTest):
    """
    Test hardware configuration application.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.provider = FakeHardwareConfigProvider("motion_controller")
        self.service = HardwareConfigurationService([self.provider])
    
    def test_apply_config(self):
        """
        Test applying configuration to hardware.
        """
        self.log_divider("Apply Configuration")
        
        config = {
            "speed": 5.0,
            "acceleration": 2.0,
            "hs": 100  # Special parameter for verification
        }
        
        self.log_interaction("Test", "CALL", "HardwareService", f"apply_config('motion_controller', config)")
        self.service.apply_config("motion_controller", config)
        
        # Verify config was applied
        self.log_interaction("Test", "ASSERT", "Provider", "Config applied",
                           {"applied": self.provider.applied_config}, expect=config, got=self.provider.applied_config)
        
        self.assertEqual(self.provider.applied_config["speed"], 5.0)
        self.assertEqual(self.provider.applied_config["acceleration"], 2.0)
        self.assertEqual(self.provider.applied_hs, 100)
    
    def test_apply_config_unknown_hardware(self):
        """
        Test applying config to unknown hardware (should raise KeyError).
        """
        self.log_divider("Test Unknown Hardware")
        
        config = {"param": "value"}
        
        self.log_interaction("Test", "CALL", "HardwareService", "apply_config('unknown', config)")
        
        with self.assertRaises(KeyError):
            self.service.apply_config("unknown_hardware", config)
        
        self.log_interaction("Test", "ASSERT", "HardwareService", "KeyError raised for unknown hardware")


if __name__ == '__main__':
    unittest.main()

