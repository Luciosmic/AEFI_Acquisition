"""
CubeVisualizerService — application service implementation.

Orchestrates the domain (sensor_rotation) and the renderer port without
knowing about PyVista or Qt widgets.
"""
from .i_api_cube_visualizer_service import IApiCubeVisualizerService
from .dtos.update_angles_request_dto import UpdateAnglesRequestDto
from .dtos.sensor_orientation_dto import SensorOrientationDto
from .ports.i_cube_renderer import ICubeRenderer
from ...domain.sensor_rotation import (
    rotation_from_euler_xyz,
    get_default_theta_x,
    get_default_theta_y,
)


class CubeVisualizerService(IApiCubeVisualizerService):
    """
    Application service orchestrating sensor orientation and rendering.

    Receives DTOs from the Interface layer, delegates math to Domain,
    delegates rendering to Infrastructure via ICubeRenderer port.
    """

    def __init__(self, renderer: ICubeRenderer):
        self._theta_x: float = get_default_theta_x()
        self._theta_y: float = get_default_theta_y()
        self._theta_z: float = 0.0
        self._renderer = renderer

    def update_angles(self, request: UpdateAnglesRequestDto) -> SensorOrientationDto:
        self._theta_x = request.theta_x
        self._theta_y = request.theta_y
        self._theta_z = request.theta_z
        self._render()
        return self._to_dto()

    def reset_to_default(self) -> SensorOrientationDto:
        self._theta_x = get_default_theta_x()
        self._theta_y = get_default_theta_y()
        self._theta_z = 0.0
        self._render()
        return self._to_dto()

    def get_current_orientation(self) -> SensorOrientationDto:
        return self._to_dto()

    def reset_camera_view(self, view_name: str) -> None:
        self._renderer.reset_camera_view(view_name)

    # ---- private ----

    def _render(self) -> None:
        rotation = rotation_from_euler_xyz(self._theta_x, self._theta_y, self._theta_z)
        self._renderer.update_view(rotation)

    def _to_dto(self) -> SensorOrientationDto:
        return SensorOrientationDto(
            theta_x=self._theta_x,
            theta_y=self._theta_y,
            theta_z=self._theta_z,
        )
