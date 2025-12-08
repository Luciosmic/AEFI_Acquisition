from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple
import math


class ExcitationParameters:
    """Parameters for the electric field excitation."""
    
    def __init__(self, excitation_mode: ExcitationMode, phase_dds1_rad: float, phase_dds2_rad: float):
        self.excitation_mode = excitation_mode
        self.phase_dds1_rad = phase_dds1_rad
        self.phase_dds2_rad = phase_dds2_rad


class ExcitationMode(Enum):
    """Modes of excitation for the 4-sphere generator."""
    OFF = auto()
    X_DIR = auto()
    Y_DIR = auto()
    CIRCULAR_PLUS = auto()
    CIRCULAR_MINUS = auto()
    CUSTOM = auto()

@dataclass(frozen=True)
class ExcitationConfig:
    """Configuration for the electric field excitation.
    
    Encapsulates the logic for setting the phases to achieve 
    the desired field direction. Uses radians (physical unit),
    not hardware-specific DDS values.
    """
    mode: ExcitationMode
    phase_dds1_rad: float = 0.0  # Phase in radians
    phase_dds2_rad: float = 0.0  # Phase in radians
    
    @classmethod
    def from_mode(cls, mode: ExcitationMode) -> 'ExcitationConfig':
        """Factory method to create a config from a high-level mode."""
        if mode == ExcitationMode.X_DIR:
            # In Phase
            return cls(mode, phase_dds1_rad=0.0, phase_dds2_rad=mmath.pi)
        elif mode == ExcitationMode.Y_DIR:
            # Opposition (180°)
            return cls(mode, phase_dds1_rad=0.0, phase_dds2_rad=0.0)
        elif mode == ExcitationMode.CIRCULAR_PLUS:
            # Quadrature +90°
            return cls(mode, phase_dds1_rad=0.0, phase_dds2_rad=math.pi/2)
        elif mode == ExcitationMode.CIRCULAR_MINUS:
            # Quadrature -90° (270°)
            return cls(mode, phase_dds1_rad=0.0, phase_dds2_rad=3*math.pi/2)
        elif mode == ExcitationMode.OFF:
            return cls(mode, phase_dds1_rad=0.0, phase_dds2_rad=0.0)
        else:
            # Custom mode requires manual instantiation
            return cls(mode, phase_dds1_rad=0.0, phase_dds2_rad=0.0)
    
    def get_phases_degrees(self) -> Tuple[float, float]:
        """Return phases in degrees for display/debugging."""
        return (math.degrees(self.phase_dds1_rad), 
                math.degrees(self.phase_dds2_rad))

