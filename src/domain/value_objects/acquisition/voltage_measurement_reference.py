"""
Domain: Acquisition - Voltage Measurement Reference

Responsibility:
    Encapsulates all calibration parameters for signal processing.
    Immutable value object that stores noise offset, phase angles, and primary field offset.

Rationale:
    - Encapsulates all calibration parameters in a single object
    - Immutable for consistency
    - Includes position and excitation parameters for traceability
    - Facilitates future persistence (save/load calibrations)
    - Reusable and testable

Design:
    - Frozen dataclass (immutable)
    - Builder pattern with `with_*` methods for creating new instances
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict
from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from .voltage_measurement import VoltageMeasurement


@dataclass(frozen=True)
class VoltageMeasurementReference:
    """Reference calibration parameters for signal processing.
    
    Encapsulates all parameters needed to correct raw measurements:
    - Noise offset (zero calibration)
    - Phase angles (phase alignment)
    - Primary field offset (tare)
    - Calibration context (position, excitation, timestamp)
    """
    
    # Calibration parameters
    noise_offset: Optional[VoltageMeasurement] = None
    phase_angles: Dict[str, float] = field(default_factory=dict)  # {'x': float, 'y': float, 'z': float} in radians
    primary_offset: Optional[VoltageMeasurement] = None
    
    # Metadata
    calibration_timestamp: datetime = field(default_factory=datetime.now)
    calibration_author: Optional[str] = None
    
    # Traceability
    calibration_position: Optional[Position2D] = None
    excitation_parameters: Optional[ExcitationParameters] = None
    
    def is_noise_calibrated(self) -> bool:
        """Check if noise offset is defined."""
        return self.noise_offset is not None
    
    def is_phase_calibrated(self) -> bool:
        """Check if all 3 phase angles are defined."""
        return len(self.phase_angles) == 3 and all(axis in self.phase_angles for axis in ['x', 'y', 'z'])
    
    def is_primary_calibrated(self) -> bool:
        """Check if primary offset is defined."""
        return self.primary_offset is not None
    
    def with_noise_offset(self, offset: VoltageMeasurement) -> 'VoltageMeasurementReference':
        """
        Create a new reference with noise_offset updated.
        
        Args:
            offset: VoltageMeasurement containing noise offsets
        
        Returns:
            New VoltageMeasurementReference with updated noise_offset
        """
        return VoltageMeasurementReference(
            noise_offset=offset,
            phase_angles=self.phase_angles.copy(),
            primary_offset=self.primary_offset,
            calibration_timestamp=self.calibration_timestamp,
            calibration_author=self.calibration_author,
            calibration_position=self.calibration_position,
            excitation_parameters=self.excitation_parameters,
        )
    
    def with_phase_angles(self, angles: Dict[str, float]) -> 'VoltageMeasurementReference':
        """
        Create a new reference with phase_angles updated.
        
        Args:
            angles: Dict with keys 'x', 'y', 'z' and values in radians
        
        Returns:
            New VoltageMeasurementReference with updated phase_angles
        """
        new_angles = self.phase_angles.copy()
        new_angles.update(angles)
        return VoltageMeasurementReference(
            noise_offset=self.noise_offset,
            phase_angles=new_angles,
            primary_offset=self.primary_offset,
            calibration_timestamp=self.calibration_timestamp,
            calibration_author=self.calibration_author,
            calibration_position=self.calibration_position,
            excitation_parameters=self.excitation_parameters,
        )
    
    def with_primary_offset(self, offset: VoltageMeasurement) -> 'VoltageMeasurementReference':
        """
        Create a new reference with primary_offset updated.
        
        Args:
            offset: VoltageMeasurement containing primary field offsets
        
        Returns:
            New VoltageMeasurementReference with updated primary_offset
        """
        return VoltageMeasurementReference(
            noise_offset=self.noise_offset,
            phase_angles=self.phase_angles.copy(),
            primary_offset=offset,
            calibration_timestamp=self.calibration_timestamp,
            calibration_author=self.calibration_author,
            calibration_position=self.calibration_position,
            excitation_parameters=self.excitation_parameters,
        )
    
    def with_calibration_context(
        self,
        position: Optional[Position2D],
        excitation: Optional[ExcitationParameters]
    ) -> 'VoltageMeasurementReference':
        """
        Create a new reference with calibration context updated.
        
        Args:
            position: Position where calibration was performed
            excitation: Excitation parameters during calibration
        
        Returns:
            New VoltageMeasurementReference with updated context
        """
        return VoltageMeasurementReference(
            noise_offset=self.noise_offset,
            phase_angles=self.phase_angles.copy(),
            primary_offset=self.primary_offset,
            calibration_timestamp=self.calibration_timestamp,
            calibration_author=self.calibration_author,
            calibration_position=position,
            excitation_parameters=excitation,
        )
