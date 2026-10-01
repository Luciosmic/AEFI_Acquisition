"""
CubeMeshFactory — infrastructure/rendering layer.

Responsibility: Create and transform PyVista meshes.
This layer is the ONLY place allowed to import pyvista.
"""
import numpy as np
import pyvista as pv
from scipy.spatial.transform import Rotation as R


# Positive-face color per sensor axis: X blue, Y yellow, Z red (same as the arrows)
AXIS_COLORS = ((0.3, 0.6, 1.0), (1.0, 0.9, 0.2), (1.0, 0.2, 0.2))
# Green electrical tape on the bench's negative faces, mirrored as a disc on each one
MARKER_COLOR = '#2E7D32'
MARKER_RADIUS_RATIO = 0.25   # disc radius / cube side
MARKER_OFFSET_RATIO = 0.002  # lift off the face / cube side (avoids z-fighting)


def create_colored_cube(size: float = 1.0) -> pv.PolyData:
    """
    Create a cube with axis-coded face colors (sign shown by the markers).
    See cube_mesh_factory_intention.md.
    """
    cube = pv.Cube(x_length=size, y_length=size, z_length=size, center=(0, 0, 0))
    cube.cell_data["colors"] = np.array(
        [AXIS_COLORS[int(np.argmax(np.abs(n)))] for n in cube.cell_normals]
    )
    return cube


def create_negative_face_markers(size: float = 1.0) -> pv.PolyData:
    """One green-tape disc centered on each negative face (−X, −Y, −Z), merged."""
    plane = size / 2 + MARKER_OFFSET_RATIO * size
    discs = []
    for axis in range(3):
        normal = np.zeros(3)
        normal[axis] = -1.0
        discs.append(pv.Disc(center=normal * plane, inner=0.0,
                             outer=MARKER_RADIUS_RATIO * size, normal=normal, c_res=48))
    return pv.merge(discs)


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
