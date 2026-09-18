import logging
from typing import Dict, Any, List
from application.services.hardware_configuration_service.ports.i_hardware_advanced_configurator import IHardwareAdvancedConfigurator
from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import HardwareAdvancedParameterSchema

logger = logging.getLogger(__name__)

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
    def get_parameter_specs() -> List[HardwareAdvancedParameterSchema]:
        return []
        
    def apply_config(self, config: Dict[str, Any]) -> None:
        logger.info(f"apply_config[{self._hardware_id}]: Applying config: {config}")
        self.applied_config.update(config)

        # Specific capture for verification
        if 'hs' in config:
            logger.debug(f"apply_config[{self._hardware_id}]: captured 'hs' for verification: {config['hs']}")
            self.applied_hs = config['hs']

    def save_config_as_default(self, config: Dict[str, Any]) -> None:
        logger.info(f"save_config_as_default[{self._hardware_id}]: Saving as default: {config}")

    def reset_to_default(self) -> None:
        logger.info(f"reset_to_default[{self._hardware_id}]: Reset to default")
        self.applied_config = {}
