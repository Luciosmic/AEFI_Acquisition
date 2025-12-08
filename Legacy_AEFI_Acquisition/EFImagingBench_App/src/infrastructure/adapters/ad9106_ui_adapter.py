"""
Example: AD9106 UI Adapter

Demonstrates how adapters expose their UI requirements.

Responsibility:
- Define UI parameter specifications for AD9106
- Provide hardware-specific validation
- Translate UI config to hardware commands

Rationale:
- Infrastructure layer defines its own UI constraints
- Keeps hardware details out of presentation layer
- Single source of truth for AD9106 parameters

Design:
- Static method returns ParameterSpec list
- Validation method checks hardware constraints
- Apply method sends config to hardware
"""

from typing import List, Tuple, Dict, Any
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from interface.hardware_configuration_tabs.parameter_spec import ParameterSpec


class AD9106UIAdapter:
    """
    UI Adapter for AD9106 DDS.
    
    Exposes parameter specifications for UI generation.
    """
    
    @staticmethod
    def get_parameter_specs() -> List[ParameterSpec]:
        """
        Get UI parameter specifications for AD9106.
        
        Returns:
            List of ParameterSpec for UI generation
        """
        return [
            # Frequency (global for all DDS)
            ParameterSpec(
                name='freq_hz',
                label='Frequency',
                type='spinbox',
                default=1000,
                range=(100, 10000),
                unit='Hz',
                tooltip='Global frequency for all DDS outputs'
            ),
            
            # DDS 1
            ParameterSpec(
                name='gain_dds1',
                label='DDS1 Gain',
                type='spinbox',
                default=8192,
                range=(0, 16383),
                tooltip='Gain for DDS channel 1 (0-16383)'
            ),
            ParameterSpec(
                name='phase_dds1',
                label='DDS1 Phase',
                type='spinbox',
                default=0,
                range=(0, 65535),
                tooltip='Phase for DDS channel 1 (0-65535, 0-360°)'
            ),
            
            # DDS 2
            ParameterSpec(
                name='gain_dds2',
                label='DDS2 Gain',
                type='spinbox',
                default=8192,
                range=(0, 16383),
                tooltip='Gain for DDS channel 2'
            ),
            ParameterSpec(
                name='phase_dds2',
                label='DDS2 Phase',
                type='spinbox',
                default=0,
                range=(0, 65535),
                tooltip='Phase for DDS channel 2'
            ),
            
            # DDS 3
            ParameterSpec(
                name='gain_dds3',
                label='DDS3 Gain',
                type='spinbox',
                default=8192,
                range=(0, 16383),
                tooltip='Gain for DDS channel 3'
            ),
            ParameterSpec(
                name='phase_dds3',
                label='DDS3 Phase',
                type='spinbox',
                default=0,
                range=(0, 65535),
                tooltip='Phase for DDS channel 3'
            ),
            
            # DDS 4
            ParameterSpec(
                name='gain_dds4',
                label='DDS4 Gain',
                type='spinbox',
                default=8192,
                range=(0, 16383),
                tooltip='Gain for DDS channel 4'
            ),
            ParameterSpec(
                name='phase_dds4',
                label='DDS4 Phase',
                type='spinbox',
                default=0,
                range=(0, 65535),
                tooltip='Phase for DDS channel 4'
            ),
        ]
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate configuration against hardware constraints.
        
        This is Level 2 validation (Adapter level) - hardware constraints.
        
        Args:
            config: Configuration dictionary
        
        Returns:
            (is_valid, error_message)
        
        Example hardware constraints:
            - Certain freq/gain combinations may be invalid
            - Phase relationships may have constraints
        """
        # Example: High frequency with high gain may be problematic
        freq = config.get('freq_hz', 0)
        
        for i in range(1, 5):
            gain = config.get(f'gain_dds{i}', 0)
            
            if freq > 5000 and gain > 12000:
                return False, f"DDS{i}: Gain too high for frequency > 5kHz (max 12000)"
        
        # Example: Check phase coherence (if needed)
        # phases = [config.get(f'phase_dds{i}', 0) for i in range(1, 5)]
        # if some_phase_constraint_violated(phases):
        #     return False, "Phase configuration invalid"
        
        return True, ""
    
    def apply_config(self, config: Dict[str, Any]) -> None:
        """
        Apply configuration to hardware.
        
        Args:
            config: Validated configuration dictionary
        
        Raises:
            HardwareConfigError: If application fails
        """
        # Validate first
        is_valid, msg = self.validate_config(config)
        if not is_valid:
            raise ValueError(f"Invalid configuration: {msg}")
        
        # Apply to hardware
        print(f"[AD9106] Applying config: {config}")
        
        # TODO: Actual hardware communication
        # self._set_frequency(config['freq_hz'])
        # for i in range(1, 5):
        #     self._set_dds_gain(i, config[f'gain_dds{i}'])
        #     self._set_dds_phase(i, config[f'phase_dds{i}'])
