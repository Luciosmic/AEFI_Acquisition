"""
Value object representing the sensor orientation in Euler angles.

Pure domain logic - no dependencies on infrastructure or UI.
"""
import math
from dataclasses import dataclass


def _get_default_theta_y() -> float:
    """Retourne l'angle Y par défaut (~35.26°)."""
    return math.degrees(math.atan(1 / math.sqrt(2)))


@dataclass(frozen=True)
class SensorOrientation:
    """
    Orientation du sensor en angles d'Euler.
    
    Immutable value object - défini uniquement par ses valeurs.
    """
    theta_x: float
    theta_y: float
    theta_z: float
    
    @classmethod
    def default(cls):
        """Crée une orientation par défaut."""
        return cls(
            theta_x=0.0,
            theta_y=_get_default_theta_y(),
            theta_z=0.0
        )

