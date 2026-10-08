"""Tests cube_mesh_factory : couleur par axe, marqueur vert sur les faces négatives."""
import numpy as np

from interface.widgets.sensor_orientation_view.cube_mesh_factory import (
    AXIS_COLORS,
    create_colored_cube,
)


def _color_of_face(cube, axis: int, sign: int) -> np.ndarray:
    normals = cube.cell_normals
    idx = next(i for i, n in enumerate(normals) if round(n[axis]) == sign)
    return cube.cell_data["colors"][idx]


def test_both_faces_of_an_axis_have_the_axis_color():
    cube = create_colored_cube()
    for axis in range(3):
        for sign in (+1, -1):
            np.testing.assert_allclose(_color_of_face(cube, axis, sign), AXIS_COLORS[axis])


def test_one_green_marker_on_each_negative_face_and_none_on_positive_faces():
    from interface.widgets.sensor_orientation_view.cube_mesh_factory import (
        MARKER_OFFSET_RATIO,
        create_negative_face_markers,
    )

    markers = create_negative_face_markers(size=1.0)
    plane = 0.5 + MARKER_OFFSET_RATIO
    pts = markers.points
    for axis in range(3):
        on_negative_face = np.isclose(pts[:, axis], -plane)
        assert on_negative_face.any()
        # disc lies inside the face, centered on it
        others = [a for a in range(3) if a != axis]
        np.testing.assert_allclose(pts[on_negative_face][:, others].mean(axis=0), 0.0, atol=1e-6)
        assert (np.abs(pts[on_negative_face][:, others]) < 0.5).all()
    assert (pts < plane - 1e-9).all()  # nothing on a positive face


def test_apply_mounting_matrix_maps_sensor_axes_to_the_columns_of_p():
    import pyvista as pv
    from interface.widgets.sensor_orientation_view.cube_mesh_factory import apply_mounting_matrix

    p_rz90 = ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))  # Rz(90°)
    point = pv.PolyData(np.array([[1.0, 0.0, 0.0]]))
    np.testing.assert_allclose(apply_mounting_matrix(point, p_rz90).points[0], [0.0, 1.0, 0.0], atol=1e-12)
