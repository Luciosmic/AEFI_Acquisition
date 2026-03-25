"""
Visualisation 3D du cube senseur.

Couches : domain/, application/, infrastructure/, interface/.
"""

from .application.cube_visualizer_service.dtos.sensor_orientation_dto import SensorOrientationDto
from .domain.sensor_rotation import get_default_theta_y, rotation_from_euler_xyz
from .infrastructure.rendering.cube_mesh_factory import apply_rotation_to_mesh, create_colored_cube
from .infrastructure.rendering.cube_visualizer_adapter_pyvista import CubeVisualizerAdapter
from .interface.cube_visualizer_presenter import CubeVisualizerPresenter

# Compat : ancien nom `create_rotation_from_euler_xyz`
create_rotation_from_euler_xyz = rotation_from_euler_xyz
SensorOrientation = SensorOrientationDto

__all__ = [
    "apply_rotation_to_mesh",
    "create_colored_cube",
    "create_rotation_from_euler_xyz",
    "CubeVisualizerAdapter",
    "CubeVisualizerPresenter",
    "get_default_theta_y",
    "rotation_from_euler_xyz",
    "SensorOrientation",
    "SensorOrientationDto",
]
