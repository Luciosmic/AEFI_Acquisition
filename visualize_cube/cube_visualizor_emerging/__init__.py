"""
Module de visualisation du cube sensor.

Architecture:
- cube_geometry.py: Mathématiques et géométrie
- cube_visualizer_presenter.py: Logique métier (Presenter)
- cube_visualizer_adapter.py: Interface PyVista (Adapter)
"""
from cube_geometry import (
    create_colored_cube,
    apply_rotation_to_mesh,
    create_rotation_from_euler_xyz,
    get_default_theta_y
)
from cube_visualizer_presenter import (
    CubeVisualizerPresenter,
    SensorOrientation
)
from cube_visualizer_adapter import CubeVisualizerAdapter

__all__ = [
    'create_colored_cube',
    'apply_rotation_to_mesh',
    'create_rotation_from_euler_xyz',
    'get_default_theta_y',
    'CubeVisualizerPresenter',
    'SensorOrientation',
    'CubeVisualizerAdapter',
]

