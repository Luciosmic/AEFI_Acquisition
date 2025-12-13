from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Dict, Any, Optional

from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
from domain.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    HardwareAdvancedParameterSchema, 
    NumberParameterSchema, 
    EnumParameterSchema, 
    BooleanParameterSchema,
    ParameterType
)
from .parameter_spec import ParameterSpec


class GenericHardwareConfigPresenter(QObject):
    """
    Presenter for the Generic Hardware Configuration UI.
    
    Responsibility:
    - Expose available hardware IDs.
    - Provide ParameterSpecs for a selected hardware.
    - Apply configuration changes via the HardwareConfigurationService.
    """
    
    # Signals
    hardware_list_updated = pyqtSignal(list) # list of str (hardware_ids)
    specs_loaded = pyqtSignal(str, list)     # hardware_id, list[ParameterSpec]
    status_message = pyqtSignal(str)         # User feedback
    
    def __init__(self, config_service: HardwareConfigurationService):
        super().__init__()
        self._service = config_service
        self._current_hardware_id: Optional[str] = None

    def refresh_hardware_list(self):
        """Fetch available hardware IDs and emit signal."""
        ids = self._service.list_hardware_ids()
        self.hardware_list_updated.emit(ids)

    def select_hardware(self, hardware_id: str):
        """
        User selected a hardware ID. 
        Load specs and emit them to View.
        """
        if hardware_id not in self._service.list_hardware_ids():
            self.status_message.emit(f"Error: Hardware '{hardware_id}' not found.")
            return
            
        self._current_hardware_id = hardware_id
        
        try:
            # Service -> Port -> Adapter returns List[HardwareAdvancedParameterSchema]
            domain_specs = self._service.get_parameter_specs(hardware_id)
            
            # Convert to UI ParameterSpecs
            ui_specs = self._convert_to_ui_specs(domain_specs)
            
            self.specs_loaded.emit(hardware_id, ui_specs)
            self.status_message.emit(f"Loaded configuration for {hardware_id}")
            
        except Exception as e:
            self.status_message.emit(f"Error loading specs: {e}")

    def apply_configuration(self, config: Dict[str, Any]):
        """
        Apply configuration to the currently selected hardware.
        """
        if not self._current_hardware_id:
            self.status_message.emit("Error: No hardware selected.")
            return
            
        try:
            self._service.apply_config(self._current_hardware_id, config)
            self.status_message.emit(f"Configuration applied to {self._current_hardware_id}")
            print(f"[Presenter] Applied config to {self._current_hardware_id}: {config}")
        except Exception as e:
            self.status_message.emit(f"Error applying config: {e}")

    def _convert_to_ui_specs(self, domain_specs: List[HardwareAdvancedParameterSchema]) -> List[ParameterSpec]:
        """Convert domain schemas to UI ParameterSpecs."""
        ui_specs = []
        
        for ds in domain_specs:
            widget_type = 'lineedit' # Default
            options = None
            rng = None
            
            if isinstance(ds, NumberParameterSchema):
                widget_type = 'spinbox'
                rng = (ds.min_value, ds.max_value)
            elif isinstance(ds, EnumParameterSchema):
                widget_type = 'combo'
                options = list(ds.choices)
            elif isinstance(ds, BooleanParameterSchema):
                widget_type = 'checkbox'
            
            spec = ParameterSpec(
                name=ds.key,
                label=ds.display_name,
                type=widget_type,
                default=ds.default_value,
                range=rng,
                options=options,
                unit=getattr(ds, 'unit', None),
                tooltip=ds.description
            )
            ui_specs.append(spec)
            
        return ui_specs
