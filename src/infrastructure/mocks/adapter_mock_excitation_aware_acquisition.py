"""
Mock: Excitation-Aware Acquisition Port

Responsibility:
    - Integrates acquisition and excitation systems seamlessly
    - Applies excitation-dependent offset to acquisition measurements
    - Provides configurable offset ratio for real/quadrature components

Rationale:
    - Simulates the physical coupling between excitation and acquisition
    - After synchronous detection, signal characteristics are tied to excitation mode
    - Frequency has no impact (processing occurs after synchronous detection)

Design:
    - Wraps an IAcquisitionPort to intercept measurements
    - Observes excitation changes via IExcitationPort or direct parameter updates
    - Applies 3D offset vector (X, Y, Z) to real part of signal
    - Configurable ratio (e.g., 0.9 = 90% real, 10% quadrature)
    - Separation function to isolate and equalize offset vectors

Technical Details:
    - Offset vector is applied to in-phase components only (by default)
    - Ratio controls contribution: ratio * offset to real, (1-ratio) * offset to quadrature
    - Initial mapping: X_DIR -> (1,0,0), Y_DIR -> (0,0,1)
    - Separation function allows future enhancements where vectors may differ
"""

from typing import Tuple, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from scipy.spatial.transform import Rotation as R

from src.application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from application.services.excitation_configuration_service.i_excitation_port import IExcitationPort
from domain.models.aefi_device.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.models.aefi_device.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.models.aefi_device.value_objects.excitation.excitation_mode import ExcitationMode


@dataclass
class OffsetVector3D:
    """3D offset vector (X, Y, Z) for applying excitation-dependent offsets."""
    x: float
    y: float
    z: float
    
    def scale(self, factor: float) -> 'OffsetVector3D':
        """Scale the vector by a factor."""
        return OffsetVector3D(self.x * factor, self.y * factor, self.z * factor)
    
    def __add__(self, other: 'OffsetVector3D') -> 'OffsetVector3D':
        """Add two vectors."""
        return OffsetVector3D(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __mul__(self, scalar: float) -> 'OffsetVector3D':
        """Multiply vector by scalar."""
        return OffsetVector3D(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __rmul__(self, scalar: float) -> 'OffsetVector3D':
        """Right multiplication by scalar."""
        return self.__mul__(scalar)


class ExcitationAwareAcquisitionPort(IAcquisitionPort):
    """
    Mock acquisition port that applies excitation-dependent offsets.
    
    This service integrates acquisition and excitation by:
    1. Wrapping a base acquisition port
    2. Observing excitation changes
    3. Applying a 3D offset vector to measurements based on excitation mode
    4. Using configurable ratio for real/quadrature contribution
    
    Usage:
        base_port = RandomNoiseAcquisitionPort()
        excitation_port = MockExcitationPort()
        aware_port = ExcitationAwareAcquisitionPort(base_port, excitation_port)
        
        # Set excitation
        excitation_port.apply_excitation(ExcitationParameters(...))
        
        # Acquire sample (will have offset applied)
        measurement = aware_port.acquire_sample()
    """
    
    # Default excitation mode to offset vector mapping
    DEFAULT_EXCITATION_OFFSET_MAP: Dict[ExcitationMode, OffsetVector3D] = {
        ExcitationMode.X_DIR: OffsetVector3D(1.0, 0.0, 0.0),
        ExcitationMode.Y_DIR: OffsetVector3D(0.0, 1.0, 0.0),  # Note: Y_DIR maps to Z offset
        ExcitationMode.CIRCULAR_PLUS: OffsetVector3D(0.0, 0.0, 0.0),  # No offset for circular
        ExcitationMode.CIRCULAR_MINUS: OffsetVector3D(0.0, 0.0, 0.0),  # No offset for circular
        ExcitationMode.CUSTOM: OffsetVector3D(0.0, 0.0, 0.0),  # No offset for custom
    }
    
    def __init__(
        self,
        base_acquisition_port: IAcquisitionPort,
        excitation_port: Optional[IExcitationPort] = None,
        real_ratio: float = 0.9,
        phase_default_ratio: Optional[float] = None,
        offset_scale: float = 1.0,
        excitation_offset_map: Optional[Dict[ExcitationMode, OffsetVector3D]] = None
    ):
        """
        Initialize excitation-aware acquisition port.
        
        Args:
            base_acquisition_port: Base acquisition port to wrap
            excitation_port: Optional excitation port to observe (if None, use manual updates)
            real_ratio: Ratio for real component (0.0-1.0). 0.9 = 90% real, 10% quadrature
            phase_default_ratio: Alias for real_ratio (if provided, overrides real_ratio)
            offset_scale: Global scaling factor for offset magnitude
            excitation_offset_map: Custom mapping from excitation mode to offset vector
        """
        self._base_port = base_acquisition_port
        self._excitation_port = excitation_port
        # Use phase_default_ratio if provided, otherwise use real_ratio
        self._real_ratio = phase_default_ratio if phase_default_ratio is not None else real_ratio
        self._offset_scale = offset_scale
        self._excitation_offset_map = excitation_offset_map or self.DEFAULT_EXCITATION_OFFSET_MAP.copy()
        
        # Current excitation state (tracked manually if no port provided)
        self._current_excitation: Optional[ExcitationParameters] = None
        
        # Separation vectors (for future enhancements)
        self._separation_vectors: Dict[ExcitationMode, OffsetVector3D] = {}
        self._equalization_factors: Dict[ExcitationMode, float] = {}
        
        # Physical Sensor Orientation (Identity by default)
        self._sensor_rotation = R.identity()
    
    def acquire_sample(self) -> VoltageMeasurement:
        """
        Acquire a sample and apply excitation-dependent offset.
        
        Returns:
            VoltageMeasurement with offset applied to in-phase components
        """
        # Get base measurement
        base_measurement = self._base_port.acquire_sample()
        
        # Get current excitation (from port or manual tracking)
        excitation = self._get_current_excitation()
        
        # Debug: Check if excitation is being read correctly
        if excitation:
            # Only print occasionally to avoid spam (every 20th sample at 20Hz = once per second)
            import random
            if random.random() < 0.05:  # 5% chance = roughly once per second at 20Hz
                print(f"[ExcitationAware] Sample acquired with excitation: {excitation.mode.name}, level={excitation.level.value}%")
        
        # Apply offset if excitation is active
        if excitation and excitation.level.value > 0:
            offset_vector = self._get_offset_vector(excitation.mode)
            
            if offset_vector and (offset_vector.x != 0 or offset_vector.y != 0 or offset_vector.z != 0):
                # Scale offset by excitation level and global scale
                level_factor = excitation.level.value / 100.0
                scaled_offset = offset_vector.scale(self._offset_scale * level_factor)
                
                # Apply separation and equalization if configured
                scaled_offset = self._apply_separation_equalization(excitation.mode, scaled_offset)
                
                # Apply offset to measurement
                return self._apply_offset_to_measurement(base_measurement, scaled_offset)
        elif excitation and excitation.level.value == 0:
            # Debug: Occasionally log when excitation is at 0%
            import random
            if random.random() < 0.01:  # 1% chance
                print(f"[ExcitationAware] Excitation at 0%, no offset applied")
        
        return base_measurement
    
    def is_ready(self) -> bool:
        """Check if base acquisition port is ready."""
        return self._base_port.is_ready()
    
    def get_quantification_noise(self) -> float:
        """Get quantification noise from base port."""
        if hasattr(self._base_port, 'get_quantification_noise'):
            return self._base_port.get_quantification_noise()
        return 0.0
    
    def set_excitation_parameters(self, params: ExcitationParameters) -> None:
        """
        Manually set excitation parameters (if not using excitation port).
        
        Args:
            params: Excitation parameters to apply
        """
        self._current_excitation = params
    
    def set_real_ratio(self, ratio: float) -> None:
        """
        Set the ratio for real component contribution.
        
        Args:
            ratio: Ratio (0.0-1.0). 0.9 = 90% real, 10% quadrature
        """
        if not (0.0 <= ratio <= 1.0):
            raise ValueError(f"real_ratio must be between 0.0 and 1.0, got {ratio}")
        self._real_ratio = ratio
    
    def set_phase_default_ratio(self, ratio: float) -> None:
        """
        Set the default ratio between real (in-phase) and imaginary (quadrature) components.
        Alias for set_real_ratio() for clarity.
        
        Args:
            ratio: Ratio (0.0-1.0). 0.9 = 90% real (in-phase), 10% imaginary (quadrature)
        """
        self.set_real_ratio(ratio)
    
    def get_phase_default_ratio(self) -> float:
        """
        Get the current ratio between real and imaginary components.
        
        Returns:
            Current ratio (0.0-1.0) where 1.0 = 100% real, 0.0 = 100% imaginary
        """
        return self._real_ratio
    
    def set_offset_scale(self, scale: float) -> None:
        """
        Set global scaling factor for offset magnitude.
        
        Args:
            scale: Scaling factor (typically 0.0-10.0)
        """
        self._offset_scale = scale
    def set_excitation_offset(self, mode: ExcitationMode, offset: OffsetVector3D) -> None:
        """
        Set custom offset vector for a specific excitation mode.
        
        Args:
            mode: Excitation mode
            offset: 3D offset vector
        """
        self._excitation_offset_map[mode] = offset
    
    def set_separation_vector(self, mode: ExcitationMode, vector: OffsetVector3D) -> None:
        """
        Set separation vector for a specific excitation mode.
        
        Separation vectors allow isolating different components of the offset.
        This prepares for future enhancements where excitation and offset vectors may differ.
        
        Args:
            mode: Excitation mode
            vector: Separation vector
        """
        self._separation_vectors[mode] = vector
    
    def set_equalization_factor(self, mode: ExcitationMode, factor: float) -> None:
        """
        Set equalization factor for a specific excitation mode.
        
        Equalization factors allow normalizing offset magnitudes across modes.
        
        Args:
            mode: Excitation mode
            factor: Equalization factor (typically 0.0-2.0)
        """
        self._equalization_factors[mode] = factor

    def set_sensor_orientation(self, theta_x: float, theta_y: float, theta_z: float) -> None:
        """
        Set the physical orientation of the sensor in degrees (XYZ extrinsic).
        This simulates the sensor being rotated relative to the Source frame.
        The acquisition port will apply the inverse rotation to the ideal source signal.
        
        Rotations are applied around FIXED axes (extrinsic):
        - theta_x: rotation around fixed X axis
        - theta_y: rotation around fixed Y axis  
        - theta_z: rotation around fixed Z axis
        """
        self._sensor_rotation = R.from_euler('XYZ', [theta_x, theta_y, theta_z], degrees=True)
    
    def _get_current_excitation(self) -> Optional[ExcitationParameters]:
        """Get current excitation parameters from port or manual tracking."""
        if self._excitation_port and hasattr(self._excitation_port, 'last_parameters'):
            return self._excitation_port.last_parameters
        return self._current_excitation
    
    def _get_offset_vector(self, mode: ExcitationMode) -> Optional[OffsetVector3D]:
        """Get offset vector for excitation mode."""
        return self._excitation_offset_map.get(mode)
    
    def _apply_separation_equalization(
        self, 
        mode: ExcitationMode, 
        offset: OffsetVector3D
    ) -> OffsetVector3D:
        """
        Apply separation and equalization to offset vector.
        
        This function isolates and equalizes offset vectors, preparing for future
        enhancements where excitation and offset vectors may differ.
        
        Args:
            mode: Excitation mode
            offset: Base offset vector
            
        Returns:
            Processed offset vector
        """
        # Apply separation if configured
        if mode in self._separation_vectors:
            # Isolate the component along the separation vector
            # For now, simple addition (can be enhanced with projection)
            offset = offset + self._separation_vectors[mode]
        
        # Apply equalization if configured
        if mode in self._equalization_factors:
            factor = self._equalization_factors[mode]
            offset = offset * factor
        
        return offset
    
    def _apply_offset_to_measurement(
        self, 
        measurement: VoltageMeasurement, 
        offset: OffsetVector3D
    ) -> VoltageMeasurement:
        """
        Apply offset vector to voltage measurement.
        
        The offset is applied to the real (in-phase) components with the configured ratio.
        The remaining (1-ratio) is applied to quadrature components.
        
        Args:
            measurement: Base voltage measurement
            offset: 3D offset vector to apply (in Source Frame)
            
        Returns:
            New VoltageMeasurement with offset applied
        """
        # Transform offset vector from Source Frame to Sensor Frame
        # v_source (Ideal Signal) -> v_sensor (Measured Signal)
        # v_sensor = R_inv * v_source
        
        v_source = np.array([offset.x, offset.y, offset.z])
        v_sensor = self._sensor_rotation.inv().apply(v_source)
        
        # DEBUG: Print rotation info occasionally (using XYZ extrinsic convention)
        import random
        if random.random() < 0.01:  # 1% chance
            angles = self._sensor_rotation.as_euler('XYZ', degrees=True)
            print(f"[ExcitationAware] Rotation(XYZ extrinsic)={np.round(angles, 1)}. Source={np.round(v_source, 2)} -> Sensor={np.round(v_sensor, 2)}")

        
        # Use transformed vector for application
        transformed_offset = OffsetVector3D(v_sensor[0], v_sensor[1], v_sensor[2])
        
        # Calculate real and quadrature contributions
        real_offset = transformed_offset * self._real_ratio
        quad_offset = transformed_offset * (1.0 - self._real_ratio)
        
        # Apply to in-phase components
        new_x_i = measurement.voltage_x_in_phase + real_offset.x
        new_y_i = measurement.voltage_y_in_phase + real_offset.y
        new_z_i = measurement.voltage_z_in_phase + real_offset.z
        
        # Apply to quadrature components
        new_x_q = measurement.voltage_x_quadrature + quad_offset.x
        new_y_q = measurement.voltage_y_quadrature + quad_offset.y
        new_z_q = measurement.voltage_z_quadrature + quad_offset.z
        
        # Create new measurement (immutable, so we create a new one)
        return VoltageMeasurement(
            voltage_x_in_phase=new_x_i,
            voltage_x_quadrature=new_x_q,
            voltage_y_in_phase=new_y_i,
            voltage_y_quadrature=new_y_q,
            voltage_z_in_phase=new_z_i,
            voltage_z_quadrature=new_z_q,
            timestamp=measurement.timestamp,
            uncertainty_estimate_volts=measurement.uncertainty_estimate_volts,
            std_dev_x_in_phase=measurement.std_dev_x_in_phase,
            std_dev_x_quadrature=measurement.std_dev_x_quadrature,
            std_dev_y_in_phase=measurement.std_dev_y_in_phase,
            std_dev_y_quadrature=measurement.std_dev_y_quadrature,
            std_dev_z_in_phase=measurement.std_dev_z_in_phase,
            std_dev_z_quadrature=measurement.std_dev_z_quadrature,
        )

