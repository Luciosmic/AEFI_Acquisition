from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple

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
    
    Encapsulates the logic for setting the phases of the two DDS channels
    to achieve the desired field direction.
    """
    mode: ExcitationMode
    phase_dds1: int = 0
    phase_dds2: int = 0
    
    @classmethod
    def from_mode(cls, mode: ExcitationMode) -> 'ExcitationConfig':
        """Factory method to create a config from a high-level mode."""
        if mode == ExcitationMode.X_DIR:
            # In Phase
            return cls(mode, phase_dds1=0, phase_dds2=0)
        elif mode == ExcitationMode.Y_DIR:
            # Opposition
            return cls(mode, phase_dds1=0, phase_dds2=32768) # 180 degrees (assuming 16-bit phase register)
        elif mode == ExcitationMode.CIRCULAR_PLUS:
            # Quadrature +90
            return cls(mode, phase_dds1=0, phase_dds2=16384) # 90 degrees
        elif mode == ExcitationMode.CIRCULAR_MINUS:
            # Quadrature -90 (270)
            return cls(mode, phase_dds1=0, phase_dds2=49152) # 270 degrees
        elif mode == ExcitationMode.OFF:
            return cls(mode, phase_dds1=0, phase_dds2=0)
        else:
            # Custom mode requires manual instantiation
            return cls(mode, phase_dds1=0, phase_dds2=0)

    def get_phases_degrees(self) -> Tuple[float, float]:
        """Return phases in degrees for display/debugging."""
        p1 = (self.phase_dds1 / 65536.0) * 360.0
        p2 = (self.phase_dds2 / 65536.0) * 360.0
        return (p1, p2)
