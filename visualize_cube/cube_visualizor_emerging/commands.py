"""
Définitions des commandes pour le cube visualizer.

Séparé des événements pour respecter CQRS.
"""
from dataclasses import dataclass
from command_bus import CommandType, Command


@dataclass
class UpdateAnglesCommand:
    """Commande pour mettre à jour les angles de rotation."""
    theta_x: float
    theta_y: float
    theta_z: float
    
    def to_command(self) -> Command:
        """Convertit en Command générique."""
        return Command(
            command_type=CommandType.UPDATE_ANGLES,
            data={
                'theta_x': self.theta_x,
                'theta_y': self.theta_y,
                'theta_z': self.theta_z
            }
        )


@dataclass
class ResetToDefaultCommand:
    """Commande pour réinitialiser aux valeurs par défaut."""
    
    def to_command(self) -> Command:
        """Convertit en Command générique."""
        return Command(
            command_type=CommandType.RESET_TO_DEFAULT,
            data={}
        )


@dataclass
class ResetCameraViewCommand:
    """Commande pour réinitialiser la vue de la caméra."""
    view_name: str  # '3d', 'xy', 'xz', 'yz'
    
    def to_command(self) -> Command:
        """Convertit en Command générique."""
        return Command(
            command_type=CommandType.RESET_CAMERA_VIEW,
            data={'view_name': self.view_name}
        )


