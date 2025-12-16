"""
Commande pour mettre à jour les angles de rotation du sensor.
"""
from dataclasses import dataclass
from infrastructure.messaging.command_bus import Command, CommandType


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



