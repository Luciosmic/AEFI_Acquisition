"""
CubeMeshFactory — infrastructure/rendering layer.

Responsibility: Create and transform PyVista meshes.
This layer is the ONLY place allowed to import pyvista.
"""
import numpy as np
import pyvista as pv
from scipy.spatial.transform import Rotation as R


def create_colored_cube(size: float = 1.0) -> pv.PolyData:
    """
    Create a cube with axis-coded face colors.

    Color convention (at zero rotation, aligned with lab axes):
        X → Blue   Y → Yellow   Z → Red

    Args:
        size: Cube side length (default 1.0)

    Returns:
        pv.PolyData: Cube with face colors assigned
    """
    cube = pv.Cube(x_length=size, y_length=size, z_length=size, center=(0, 0, 0))

    colors = np.array([
        [0.3, 0.6, 1.0],  # +X Blue
        [0.3, 0.6, 1.0],  # -X Blue
        [1.0, 0.9, 0.2],  # +Y Yellow
        [1.0, 0.9, 0.2],  # -Y Yellow
        [1.0, 0.2, 0.2],  # +Z Red
        [1.0, 0.2, 0.2],  # -Z Red
    ])

    n = cube.n_cells
    cube.cell_data["colors"] = colors[:n]
    return cube


def apply_rotation_to_mesh(mesh: pv.PolyData, rotation: R) -> pv.PolyData:
    """
    Apply a scipy Rotation to a PyVista mesh (returns a copy).

    Args:
        mesh: Source mesh
        rotation: scipy Rotation object

    Returns:
        pv.PolyData: Rotated copy of the mesh
    """
    mesh_copy = mesh.copy()
    mesh_copy.points = rotation.apply(mesh_copy.points)
    return mesh_copy
