"""
Commande pour réinitialiser la vue de la caméra.
"""
from dataclasses import dataclass
from infrastructure.messaging.command_bus import Command, CommandType


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

