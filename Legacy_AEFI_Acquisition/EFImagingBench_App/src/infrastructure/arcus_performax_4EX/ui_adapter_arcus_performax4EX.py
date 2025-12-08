"""
Arcus Performax 4EX UI Adapter

Responsibility:
- Define UI parameter specifications for Arcus Performax 4EX motor controller
- Provide hardware-specific validation for motion parameters
- Translate UI config to motor commands

Rationale:
- Infrastructure layer defines its own UI constraints
- Keeps hardware details out of presentation layer
- Single source of truth for Arcus Performax 4EX parameters

Design:
- Static method returns ParameterSpec list
- Validation method checks hardware constraints (speed, acceleration limits)
- Apply method sends config to motor controller
"""

from typing import List, Tuple, Dict, Any
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from interface.hardware_configuration_tabs.parameter_spec import ParameterSpec


class ArcusPerformax4EXUIAdapter:
    """
    UI Adapter for Arcus Performax 4EX motor controller.
    
    Exposes parameter specifications for UI generation.
    Supports 4-axis stepper motor control with speed/acceleration parameters.
    """
    
    @staticmethod
    def get_parameter_specs() -> List[ParameterSpec]:
        """
        Get UI parameter specifications for Arcus Performax 4EX.
        
        Returns:
            List of ParameterSpec for UI generation
            
        Parameters include:
        - Speed parameters (velocity, acceleration, deceleration)
        - Jog parameters (jog speed, jog acceleration)
        - Motion limits (min/max position)
        - Homing parameters
        """
        return [
            # === Speed Parameters ===
            ParameterSpec(
                name='max_velocity',
                label='Max Velocity',
                type='spinbox',
                default=5000,
                range=(100, 50000),
                unit='steps/s',
                tooltip='Maximum motor velocity (100-50000 steps/s)'
            ),
            ParameterSpec(
                name='acceleration',
                label='Acceleration',
                type='spinbox',
                default=10000,
                range=(100, 500000),
                unit='steps/s²',
                tooltip='Motor acceleration rate (100-500000 steps/s²)'
            ),
            ParameterSpec(
                name='deceleration',
                label='Deceleration',
                type='spinbox',
                default=10000,
                range=(100, 500000),
                unit='steps/s²',
                tooltip='Motor deceleration rate (100-500000 steps/s²)'
            ),
            
            # === Jog Parameters ===
            ParameterSpec(
                name='jog_velocity',
                label='Jog Velocity',
                type='spinbox',
                default=2000,
                range=(100, 50000),
                unit='steps/s',
                tooltip='Velocity for manual jog movements'
            ),
            ParameterSpec(
                name='jog_acceleration',
                label='Jog Acceleration',
                type='spinbox',
                default=5000,
                range=(100, 500000),
                unit='steps/s²',
                tooltip='Acceleration for manual jog movements'
            ),
            
            # === Motion Limits ===
            ParameterSpec(
                name='min_position',
                label='Min Position',
                type='spinbox',
                default=0,
                range=(-1000000, 1000000),
                unit='steps',
                tooltip='Minimum allowed position (software limit)'
            ),
            ParameterSpec(
                name='max_position',
                label='Max Position',
                type='spinbox',
                default=100000,
                range=(-1000000, 1000000),
                unit='steps',
                tooltip='Maximum allowed position (software limit)'
            ),
            
            # === Homing Parameters ===
            ParameterSpec(
                name='homing_direction',
                label='Homing Direction',
                type='combo',
                default='Negative',
                options=['Positive', 'Negative'],
                tooltip='Direction to search for home switch'
            ),
            ParameterSpec(
                name='homing_velocity',
                label='Homing Velocity',
                type='spinbox',
                default=1000,
                range=(100, 10000),
                unit='steps/s',
                tooltip='Velocity during homing sequence'
            ),
            
            # === Current Settings ===
            ParameterSpec(
                name='run_current',
                label='Run Current',
                type='combo',
                default='50%',
                options=['25%', '50%', '75%', '100%'],
                tooltip='Motor current during movement'
            ),
            ParameterSpec(
                name='hold_current',
                label='Hold Current',
                type='combo',
                default='25%',
                options=['0%', '25%', '50%', '75%', '100%'],
                tooltip='Motor current when holding position'
            ),
            
            # === Microstepping ===
            ParameterSpec(
                name='microstep_resolution',
                label='Microstep Resolution',
                type='combo',
                default='1/8',
                options=['Full', '1/2', '1/4', '1/8', '1/16', '1/32', '1/64', '1/128'],
                tooltip='Microstepping resolution (higher = smoother but slower)'
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
        
        Hardware constraints:
        - Acceleration/deceleration must be reasonable for velocity
        - Jog parameters must be within motion limits
        - Position limits must be valid (min < max)
        """
        # Extract values
        max_vel = config.get('max_velocity', 5000)
        accel = config.get('acceleration', 10000)
        decel = config.get('deceleration', 10000)
        jog_vel = config.get('jog_velocity', 2000)
        jog_accel = config.get('jog_acceleration', 5000)
        min_pos = config.get('min_position', 0)
        max_pos = config.get('max_position', 100000)
        
        # Check position limits
        if min_pos >= max_pos:
            return False, f"Min position ({min_pos}) must be < max position ({max_pos})"
        
        # Check jog velocity vs max velocity
        if jog_vel > max_vel:
            return False, f"Jog velocity ({jog_vel}) cannot exceed max velocity ({max_vel})"
        
        # Check acceleration is reasonable for velocity
        # Rule of thumb: accel should allow reaching max velocity in reasonable time
        # Time to reach max velocity = max_vel / accel
        # Warn if it takes more than 10 seconds
        time_to_max_vel = max_vel / accel if accel > 0 else float('inf')
        if time_to_max_vel > 10:
            return False, f"Acceleration too low: takes {time_to_max_vel:.1f}s to reach max velocity (max 10s recommended)"
        
        # Check deceleration is reasonable
        time_to_stop = max_vel / decel if decel > 0 else float('inf')
        if time_to_stop > 10:
            return False, f"Deceleration too low: takes {time_to_stop:.1f}s to stop from max velocity (max 10s recommended)"
        
        # Check jog acceleration
        if jog_accel > accel:
            return False, f"Jog acceleration ({jog_accel}) should not exceed normal acceleration ({accel})"
        
        return True, ""
    
    def apply_config(self, config: Dict[str, Any]) -> None:
        """
        Apply configuration to Arcus Performax 4EX motor controller.
        
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
        print(f"[Arcus Performax 4EX] Applying config: {config}")
        
        # TODO: Actual hardware communication
        # self._set_velocity(config['max_velocity'])
        # self._set_acceleration(config['acceleration'])
        # self._set_deceleration(config['deceleration'])
        # self._set_jog_parameters(config['jog_velocity'], config['jog_acceleration'])
        # self._set_position_limits(config['min_position'], config['max_position'])
        # self._set_homing_parameters(config['homing_direction'], config['homing_velocity'])
        # self._set_current(config['run_current'], config['hold_current'])
        # self._set_microstepping(config['microstep_resolution'])
