from typing import Dict, Any, List
from application.services.hardware_configuration_service.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator
from application.dtos.hardware_parameter_dtos import ActionableHardwareParametersSpec

class MockHardwareConfigProvider(IHardwareAdvancedConfigurator):
    """
    Mock implementation of IHardwareAdvancedConfigurator for testing.
    Records applied configuration.
    """
    
    def __init__(self, hardware_id: str):
        self._hardware_id = hardware_id
        self.applied_config: Dict[str, Any] = {}
        # Special attributes for verification
        self.applied_hs = None
        
    @property
    def hardware_id(self) -> str:
        return self._hardware_id
    
    @property
    def display_name(self) -> str:
        return f"Mock Hardware ({self._hardware_id})"
    
    @staticmethod
    def get_parameter_specs() -> List[ActionableHardwareParametersSpec]:
        return []
        
    def apply_config(self, config: Dict[str, Any]) -> None:
        print(f"[MockProvider:{self._hardware_id}] Applying config: {config}")
        self.applied_config.update(config)
        
        # Specific capture for verification
        if 'hs' in config:
            self.applied_hs = config['hs']
