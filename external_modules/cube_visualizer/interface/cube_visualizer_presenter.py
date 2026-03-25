"""
CubeVisualizerPresenter — interface layer.

Bridges the Qt UI spinboxes to the application service (IApiCubeVisualizerService).
Uses CommandBus to send user actions, subscribes to EventBus for state updates.
"""
from ..application.cube_visualizer_service.i_api_cube_visualizer_service import IApiCubeVisualizerService
from ..application.cube_visualizer_service.dtos.update_angles_request_dto import UpdateAnglesRequestDto
from ..infrastructure.messaging.command_bus import CommandBus, Command, CommandType
from ..infrastructure.messaging.event_bus import EventBus, Event, EventType


class CubeVisualizerPresenter:
    """
    Presenter: adapts Qt spinbox signals to application service calls.

    Does NOT contain business logic — delegates everything to IApiCubeVisualizerService.
    """

    def __init__(self,
                 service: IApiCubeVisualizerService,
                 command_bus: CommandBus,
                 event_bus: EventBus):
        self._service = service
        self._command_bus = command_bus
        self._event_bus = event_bus

        # Register command handlers on the bus
        self._command_bus.register_handler(CommandType.UPDATE_ANGLES, self._handle_update_angles)
        self._command_bus.register_handler(CommandType.RESET_TO_DEFAULT, self._handle_reset)

    # ---- Inbound (called by Qt UI) ----

    def request_update_angles(self, theta_x: float, theta_y: float, theta_z: float) -> None:
        """Called by the Qt UI when spinboxes change."""
        command = Command(
            command_type=CommandType.UPDATE_ANGLES,
            data={'theta_x': theta_x, 'theta_y': theta_y, 'theta_z': theta_z}
        )
        self._command_bus.send(command)

    def request_reset(self) -> None:
        """Called by the Qt UI when Reset button is pressed."""
        command = Command(command_type=CommandType.RESET_TO_DEFAULT, data={})
        self._command_bus.send(command)

    def request_camera_view(self, view_name: str) -> None:
        """Called by the Qt UI when a camera-view button is pressed."""
        event = Event(event_type=EventType.CAMERA_VIEW_CHANGED, data={'view_name': view_name})
        self._event_bus.publish(event)

    def get_current_angles(self) -> tuple:
        """Query current angles (no side effects)."""
        dto = self._service.get_current_orientation()
        return dto.theta_x, dto.theta_y, dto.theta_z

    # ---- Handlers (from CommandBus) ----

    def _handle_update_angles(self, command: Command) -> None:
        dto = UpdateAnglesRequestDto(
            theta_x=command.data['theta_x'],
            theta_y=command.data['theta_y'],
            theta_z=command.data['theta_z'],
        )
        result = self._service.update_angles(dto)
        # Publish state change so the adapter re-renders
        self._event_bus.publish(Event(
            event_type=EventType.ANGLES_CHANGED,
            data={'theta_x': result.theta_x, 'theta_y': result.theta_y, 'theta_z': result.theta_z}
        ))

    def _handle_reset(self, command: Command) -> None:
        result = self._service.reset_to_default()
        self._event_bus.publish(Event(
            event_type=EventType.ANGLES_CHANGED,
            data={'theta_x': result.theta_x, 'theta_y': result.theta_y, 'theta_z': result.theta_z}
        ))
