"""
CommandBus minimal pour gérer les commandes de manière thread-safe.

Utilise PySide6.QtCore.QObject et Signal pour garantir l'exécution sur le thread principal Qt.
Séparé de l'EventBus pour respecter CQRS (Command Query Responsibility Segregation).
"""
from PySide6.QtCore import QObject, Signal, Qt
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum


class CommandType(Enum):
    """Types de commandes supportés."""
    UPDATE_ANGLES = "update_angles"
    RESET_TO_DEFAULT = "reset_to_default"
    RESET_CAMERA_VIEW = "reset_camera_view"


@dataclass
class Command:
    """Commande générique."""
    command_type: CommandType
    data: Dict[str, Any]


class CommandBus(QObject):
    """
    CommandBus thread-safe utilisant les signaux Qt.
    
    Garantit que tous les handlers sont exécutés sur le thread principal Qt.
    Utilisé pour les commandes (modifications d'état), séparé de l'EventBus (notifications).
    """
    
    # Signal émis quand une commande est publiée
    command_published = Signal(object)  # Command
    
    def __init__(self):
        super().__init__()
        self._handlers: Dict[CommandType, List[Callable]] = {}
        # Connecter le signal à un slot qui dispatch les commandes
        self.command_published.connect(self._dispatch_command, Qt.QueuedConnection)
    
    def register_handler(self, command_type: CommandType, handler: Callable[[Command], None]):
        """
        Enregistrer un handler pour un type de commande.
        
        Args:
            command_type: Type de commande
            handler: Fonction appelée avec la commande
        """
        if command_type not in self._handlers:
            self._handlers[command_type] = []
        self._handlers[command_type].append(handler)
    
    def unregister_handler(self, command_type: CommandType, handler: Callable[[Command], None]):
        """
        Désenregistrer un handler pour un type de commande.
        
        Args:
            command_type: Type de commande
            handler: Handler à retirer
        """
        if command_type in self._handlers:
            try:
                self._handlers[command_type].remove(handler)
            except ValueError:
                pass
    
    def send(self, command: Command):
        """
        Envoyer une commande (thread-safe).
        
        Args:
            command: Commande à envoyer
        """
        # Émettre le signal (thread-safe, sera dispatché sur le thread principal)
        self.command_published.emit(command)
    
    def _dispatch_command(self, command: Command):
        """
        Dispatch la commande aux handlers (exécuté sur le thread principal Qt).
        
        Args:
            command: Commande à dispatcher
        """
        if command.command_type in self._handlers:
            for handler in self._handlers[command.command_type]:
                try:
                    handler(command)
                except Exception as e:
                    print(f"[ERROR] Erreur dans handler pour {command.command_type}: {e}")
                    import traceback
                    traceback.print_exc()


