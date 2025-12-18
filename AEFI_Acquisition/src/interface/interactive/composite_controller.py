"""
Composite Interactive Controller

Aggregates all interactive controllers and provides unified interface.
Follows Composite pattern and ISP.
"""

from typing import Dict, Any, List, Optional
from domain.shared.events.i_domain_event_bus import IDomainEventBus
from interface.interactive.i_interactive_port import IInteractivePort, ICommandHandler, IEventPublisher


class CompositeController(IInteractivePort, ICommandHandler, IEventPublisher):
    """
    Composite controller that aggregates all specific controllers.
    
    Responsibilities:
    - Initialize all controllers with EventBus
    - Route commands to appropriate controllers
    - Aggregate event publishing
    - Manage controller lifecycle
    """
    
    def __init__(self):
        self._controllers: Dict[str, IInteractivePort] = {}
        self._event_bus: Optional[IDomainEventBus] = None
    
    def register_controller(self, controller: IInteractivePort) -> None:
        """
        Register a controller.
        
        Args:
            controller: Controller implementing IInteractivePort
        """
        name = controller.get_controller_name()
        if name in self._controllers:
            raise ValueError(f"Controller '{name}' already registered")
        self._controllers[name] = controller
    
    def get_controller(self, name: str) -> Optional[IInteractivePort]:
        """
        Get a specific controller by name.
        
        Args:
            name: Controller name
        
        Returns:
            Controller or None if not found
        """
        return self._controllers.get(name)
    
    # ==================================================================================
    # IInteractivePort Implementation
    # ==================================================================================
    
    def initialize(self, event_bus: IDomainEventBus) -> None:
        """Initialize all registered controllers with EventBus."""
        self._event_bus = event_bus
        for controller in self._controllers.values():
            controller.initialize(event_bus)
    
    def shutdown(self) -> None:
        """Shutdown all controllers."""
        for controller in self._controllers.values():
            controller.shutdown()
        self._controllers.clear()
    
    def get_controller_name(self) -> str:
        return "composite"
    
    # ==================================================================================
    # ICommandHandler Implementation
    # ==================================================================================
    
    def handle_command(self, command_type: str, command_data: Dict[str, Any]) -> None:
        """
        Route command to appropriate controller.
        
        Command format: "{controller_name}_{action}"
        Examples:
        - "scan_start" -> ScanController
        - "motion_move" -> MotionController
        - "acquisition_start" -> AcquisitionController
        """
        # Parse command: "{controller}_{action}"
        parts = command_type.split("_", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid command format: {command_type}. Expected '{{controller}}_{{action}}'")
        
        controller_name, action = parts
        
        # Get controller
        controller = self._controllers.get(controller_name)
        if not controller:
            raise ValueError(f"Unknown controller: {controller_name}")
        
        # Check if controller implements ICommandHandler
        if not isinstance(controller, ICommandHandler):
            raise ValueError(f"Controller '{controller_name}' does not implement ICommandHandler")
        
        # Route command with full type (for controller's internal routing)
        controller.handle_command(command_type, command_data)
    
    # ==================================================================================
    # IEventPublisher Implementation
    # ==================================================================================
    
    def publish_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Publish event to EventBus (if available)."""
        if self._event_bus:
            self._event_bus.publish(event_type, event_data)
    
    # ==================================================================================
    # Utility Methods
    # ==================================================================================
    
    def list_controllers(self) -> List[str]:
        """List all registered controller names."""
        return list(self._controllers.keys())
    
    def has_controller(self, name: str) -> bool:
        """Check if a controller is registered."""
        return name in self._controllers

