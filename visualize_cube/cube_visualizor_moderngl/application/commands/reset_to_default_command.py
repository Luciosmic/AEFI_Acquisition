"""
Commande pour réinitialiser les angles aux valeurs par défaut.
"""
from dataclasses import dataclass
from infrastructure.messaging.command_bus import Command, CommandType


@dataclass
class ResetToDefaultCommand:
    """Commande pour réinitialiser aux valeurs par défaut."""
    
    def to_command(self) -> Command:
        """Convertit en Command générique."""
        return Command(
            command_type=CommandType.RESET_TO_DEFAULT,
            data={}
        )



