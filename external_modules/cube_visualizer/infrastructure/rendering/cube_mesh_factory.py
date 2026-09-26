"""
CubeMeshFactory — infrastructure/rendering layer.

Responsibility: Create and transform PyVista meshes.
This layer is the ONLY place allowed to import pyvista.
"""
import numpy as np
import pyvista as pv
from scipy.spatial.transform import Rotation as R
from typing import Optional

from ...domain.cube_geometry import vertex_positions, edge_midpoints, face_centers


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


def _outward_offset(positions: dict, offset: float) -> tuple[np.ndarray, list[str]]:
    """Offset positions radially outward from the origin for label placement."""
    labels = list(positions.keys())
    pts = []
    for pos in positions.values():
        norm = np.linalg.norm(pos)
        pts.append(pos + (pos / norm) * offset if norm > 1e-9 else pos.copy())
    return np.array(pts), labels


def get_vertex_label_data(
    size: float = 1.0, rotation: Optional[R] = None
) -> tuple[np.ndarray, list[str]]:
    """
    Return (points, labels) for the 8 vertices, ready for plotter.add_point_labels().

    Points are offset slightly outward for readability. If rotation is provided,
    points are expressed in lab frame (body frame rotated).
    """
    pts, labels = _outward_offset(vertex_positions(size), offset=0.08 * size)
    if rotation is not None:
        pts = rotation.apply(pts)
    return pts, labels


def get_edge_label_data(
    size: float = 1.0, rotation: Optional[R] = None
) -> tuple[np.ndarray, list[str]]:
    """Return (points, labels) for the 12 edge midpoints."""
    pts, labels = _outward_offset(edge_midpoints(size), offset=0.06 * size)
    if rotation is not None:
        pts = rotation.apply(pts)
    return pts, labels


def get_face_label_data(
    size: float = 1.0, rotation: Optional[R] = None
) -> tuple[np.ndarray, list[str]]:
    """Return (points, labels) for the 6 face centers."""
    pts, labels = _outward_offset(face_centers(size), offset=0.05 * size)
    if rotation is not None:
        pts = rotation.apply(pts)
    return pts, labels


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
