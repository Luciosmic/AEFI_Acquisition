"""
ADS131A04 UI Adapter

Responsibility:
- Define UI parameter specifications for ADS131A04 ADC
- Provide hardware-specific validation
- Translate UI config to hardware commands

Rationale:
- Infrastructure layer defines its own UI constraints
- Keeps hardware details out of presentation layer
- Single source of truth for ADS131A04 parameters

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


class ADS131A04UIAdapter:
    """
    UI Adapter for ADS131A04 ADC.
    
    Exposes parameter specifications for UI generation.
    """
    
    @staticmethod
    def get_parameter_specs() -> List[ParameterSpec]:
        """
        Get UI parameter specifications for ADS131A04.
        
        Returns:
            List of ParameterSpec for UI generation
        """
        return [
            # Timing Configuration
            ParameterSpec(
                name='osr',
                label='Oversampling Ratio (OSR)',
                type='combo',
                default='4096',
                options=['128', '256', '512', '1024', '2048', '4096', '8192', '16384'],
                tooltip='Higher OSR = lower noise but slower sampling'
            ),
            ParameterSpec(
                name='sampling_rate',
                label='Sampling Rate',
                type='combo',
                default='8 kSPS',
                options=['1 kSPS', '2 kSPS', '4 kSPS', '8 kSPS', '16 kSPS', '32 kSPS', '64 kSPS'],
                tooltip='ADC sampling rate (samples per second)'
            ),
            
            # Gain Configuration (4 channels)
            ParameterSpec(
                name='gain_ch1',
                label='Channel 1 Gain',
                type='combo',
                default='1',
                options=['1', '2', '4', '8', '16', '32', '64', '128'],
                tooltip='Programmable gain for channel 1'
            ),
            ParameterSpec(
                name='gain_ch2',
                label='Channel 2 Gain',
                type='combo',
                default='1',
                options=['1', '2', '4', '8', '16', '32', '64', '128'],
                tooltip='Programmable gain for channel 2'
            ),
            ParameterSpec(
                name='gain_ch3',
                label='Channel 3 Gain',
                type='combo',
                default='1',
                options=['1', '2', '4', '8', '16', '32', '64', '128'],
                tooltip='Programmable gain for channel 3'
            ),
            ParameterSpec(
                name='gain_ch4',
                label='Channel 4 Gain',
                type='combo',
                default='1',
                options=['1', '2', '4', '8', '16', '32', '64', '128'],
                tooltip='Programmable gain for channel 4'
            ),
            
            # Reference Configuration
            ParameterSpec(
                name='reference_mode',
                label='Reference Mode',
                type='combo',
                default='Internal',
                options=['Internal', 'External'],
                tooltip='Voltage reference source'
            ),
            ParameterSpec(
                name='reference_voltage',
                label='Reference Voltage',
                type='combo',
                default='2.442V',
                options=['1.2V', '2.442V', '4.096V'],
                tooltip='Reference voltage level'
            ),
            
            # Digital Filter
            ParameterSpec(
                name='filter_type',
                label='Digital Filter',
                type='combo',
                default='Sinc3',
                options=['Sinc1', 'Sinc2', 'Sinc3', 'Sinc4'],
                tooltip='Digital filter type for noise reduction'
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
            - OSR and sampling rate must be compatible
            - High gain with high sampling rate may cause issues
        """
        # Extract values
        osr = int(config.get('osr', 4096))
        sampling_rate_str = config.get('sampling_rate', '8 kSPS')
        sampling_rate = int(sampling_rate_str.split()[0])  # Extract number
        
        # Check OSR vs sampling rate compatibility
        # Higher OSR requires lower sampling rate
        if osr >= 8192 and sampling_rate > 16:
            return False, f"OSR {osr} too high for sampling rate {sampling_rate_str} (max 16 kSPS)"
        
        if osr >= 4096 and sampling_rate > 32:
            return False, f"OSR {osr} too high for sampling rate {sampling_rate_str} (max 32 kSPS)"
        
        # Check gain settings
        for ch in range(1, 5):
            gain = int(config.get(f'gain_ch{ch}', 1))
            
            # High gain with high sampling rate may saturate
            if gain >= 64 and sampling_rate >= 32:
                return False, f"Ch{ch}: Gain {gain} too high for sampling rate {sampling_rate_str} (max gain 32)"
        
        return True, ""
    
    def apply_config(self, config: Dict[str, Any]) -> None:
        """
        Apply configuration to hardware.
        
        Args:
            config: Validated configuration dictionary
        
        Raises:
            ValueError: If configuration invalid
        """
        # Validate first
        is_valid, msg = self.validate_config(config)
        if not is_valid:
            raise ValueError(f"Invalid configuration: {msg}")
        
        # Apply to hardware
        print(f"[ADS131A04] Applying config: {config}")
        
        # TODO: Actual hardware communication
        # self._configure_osr(config['osr'])
        # self._configure_sampling_rate(config['sampling_rate'])
        # for ch in range(1, 5):
        #     self._set_channel_gain(ch, config[f'gain_ch{ch}'])
        # self._configure_reference(config['reference_mode'], config['reference_voltage'])
        # self._configure_filter(config['filter_type'])
