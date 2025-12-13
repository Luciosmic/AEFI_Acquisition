"""
Hardware Advanced Configuration Presenter - Interface V2

Bridges between HardwareConfigurationService and HardwareAdvancedConfigPanel.
Adapted from interface v1 for PySide6.
"""

from PySide6.QtCore import QObject, Signal, Slot
from typing import List, Dict, Any, Optional

from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema,
    NumberParameterSchema,
    EnumParameterSchema,
    BooleanParameterSchema,
)


class HardwareAdvancedConfigPresenter(QObject):
    """
    Presenter for Hardware Advanced Configuration Panel.
    
    Responsibility:
    - Expose available hardware IDs.
    - Provide parameter specs for selected hardware.
    - Apply configuration changes via HardwareConfigurationService.
    """
    
    # Signals emitted to the UI
    hardware_list_updated = Signal(list)  # list of str (hardware_ids)
    specs_loaded = Signal(str, list)  # hardware_id, list[HardwareAdvancedParameterSchema]
    status_message = Signal(str)  # User feedback
    config_applied = Signal(str)  # hardware_id
    
    def __init__(self, config_service: HardwareConfigurationService):
        super().__init__()
        self._service = config_service
        self._current_hardware_id: Optional[str] = None
    
    @Slot()
    def refresh_hardware_list(self):
        """Fetch available hardware IDs and emit signal."""
        try:
            ids = self._service.list_hardware_ids()
            self.hardware_list_updated.emit(ids)
            self.status_message.emit(f"Found {len(ids)} hardware device(s)")
        except Exception as e:
            self.status_message.emit(f"Error refreshing hardware list: {e}")
    
    @Slot(str)
    def select_hardware(self, hardware_id: str):
        """
        User selected a hardware ID.
        Load specs and emit them to View.
        
        Args:
            hardware_id: Identifier of the hardware to configure
        """
        if hardware_id not in self._service.list_hardware_ids():
            self.status_message.emit(f"Error: Hardware '{hardware_id}' not found.")
            return
        
        self._current_hardware_id = hardware_id
        
        try:
            # Service returns List[HardwareAdvancedParameterSchema]
            domain_specs = self._service.get_parameter_specs(hardware_id)
            
            self.specs_loaded.emit(hardware_id, domain_specs)
            display_name = self._service.get_hardware_display_name(hardware_id)
            self.status_message.emit(f"Loaded configuration for {display_name}")
            
        except Exception as e:
            self.status_message.emit(f"Error loading specs: {e}")
    
    @Slot(dict)
    def apply_configuration(self, config: Dict[str, Any]):
        """
        Apply configuration to the currently selected hardware.
        
        Args:
            config: Dictionary of parameter values keyed by parameter key
        """
        if not self._current_hardware_id:
            self.status_message.emit("Error: No hardware selected.")
            return
        
        try:
            self._service.apply_config(self._current_hardware_id, config)
            display_name = self._service.get_hardware_display_name(self._current_hardware_id)
            self.status_message.emit(f"Configuration applied to {display_name}")
            self.config_applied.emit(self._current_hardware_id)
        except Exception as e:
            self.status_message.emit(f"Error applying config: {e}")

