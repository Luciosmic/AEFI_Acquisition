"""
Service d'application pour la visualisation du cube sensor.

Responsabilité : Logique métier, gestion des angles, synchronisation des vues.
Utilise CommandBus pour recevoir les commandes et EventBus pour publier les événements (CQRS).
"""
from domain.value_objects.sensor_orientation import SensorOrientation
from domain.services.geometry_service import create_rotation_from_euler_xyz
from infrastructure.messaging.event_bus import EventBus, Event, EventType
from infrastructure.messaging.command_bus import CommandBus, Command, CommandType


class CubeVisualizerService:
    """
    Service gérant la logique métier de la visualisation.

    Responsabilités:
    - Gestion des angles de rotation
    - Synchronisation entre les différentes vues
    - Réception des commandes via CommandBus (CQRS)
    - Publication des événements via EventBus (CQRS)
    """

    def __init__(self, command_bus: CommandBus, event_bus: EventBus):
        """
        Args:
            command_bus: CommandBus pour recevoir les commandes (requis)
            event_bus: EventBus pour publier les événements (requis)
        """
        if command_bus is None:
            raise ValueError("CommandBus est requis pour CubeVisualizerService")
        if event_bus is None:
            raise ValueError("EventBus est requis pour CubeVisualizerService")
        
        self.command_bus = command_bus
        self.event_bus = event_bus
        self.orientation = SensorOrientation.default()
        
        # S'enregistrer comme handler pour les commandes
        self.command_bus.register_handler(CommandType.UPDATE_ANGLES, self._handle_update_angles_command)
        self.command_bus.register_handler(CommandType.RESET_TO_DEFAULT, self._handle_reset_to_default_command)
    
    def _handle_update_angles_command(self, command: Command):
        """Handler pour la commande UPDATE_ANGLES (CQRS)."""
        theta_x = command.data['theta_x']
        theta_y = command.data['theta_y']
        theta_z = command.data['theta_z']
        self._update_angles_internal(theta_x, theta_y, theta_z)
    
    def _handle_reset_to_default_command(self, command: Command):
        """Handler pour la commande RESET_TO_DEFAULT (CQRS)."""
        self._reset_to_default_internal()
    
    def _update_angles_internal(self, theta_x: float, theta_y: float, theta_z: float):
        """
        Met à jour les angles de rotation (méthode interne).
        
        Args:
            theta_x: Angle autour de X (degrés)
            theta_y: Angle autour de Y (degrés)
            theta_z: Angle autour de Z (degrés)
        """
        # Créer une nouvelle instance (immutable value object)
        self.orientation = SensorOrientation(
            theta_x=theta_x,
            theta_y=theta_y,
            theta_z=theta_z
        )
        self._publish_angles_changed_event()
    
    def _reset_to_default_internal(self):
        """Réinitialise les angles aux valeurs par défaut (méthode interne)."""
        self.orientation = SensorOrientation.default()
        self._publish_angles_changed_event()
    
    def _publish_angles_changed_event(self):
        """Publie un événement de changement d'angles via EventBus (CQRS)."""
        event = Event(
            event_type=EventType.ANGLES_CHANGED,
            data={
                'theta_x': self.orientation.theta_x,
                'theta_y': self.orientation.theta_y,
                'theta_z': self.orientation.theta_z
            }
        )
        self.event_bus.publish(event)
    
    def get_rotation(self):
        """
        Retourne l'objet Rotation actuel (Query - pas de modification d'état).
        
        Returns:
            Rotation: Objet Rotation de scipy.spatial.transform
        """
        return create_rotation_from_euler_xyz(
            self.orientation.theta_x,
            self.orientation.theta_y,
            self.orientation.theta_z
        )
    
    def get_angles(self):
        """
        Retourne les angles actuels (Query - pas de modification d'état).
        
        Returns:
            tuple: (theta_x, theta_y, theta_z)
        """
        return (
            self.orientation.theta_x,
            self.orientation.theta_y,
            self.orientation.theta_z
        )

