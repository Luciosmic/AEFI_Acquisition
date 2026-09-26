"""
CubeViewExporter — infrastructure/rendering layer.

Offscreen multi-view PNG export: generates labeled cube views for documentation.
No Qt dependency — safe to call from scripts or notebooks.

Usage:
    from cube_visualizer.infrastructure.rendering.cube_view_exporter import export_cube_views
    from cube_visualizer.domain.sensor_rotation import rotation_from_euler_xyz

    rotation = rotation_from_euler_xyz(35.26, 45.0, 0.0)
    paths = export_cube_views(rotation, output_dir="./vues_cube/")
"""
import numpy as np
import pyvista as pv
from pathlib import Path
from scipy.spatial.transform import Rotation as R

from .cube_mesh_factory import (
    create_colored_cube, apply_rotation_to_mesh,
    get_vertex_label_data, get_edge_label_data, get_face_label_data,
)


_CAMERA_POSITIONS: dict[str, list] = {
    '3d': [(3.0, -3.0, 2.0), (0, 0, 0), (0, 0, 1)],
    'xy': [(0.0,  0.0, 5.0), (0, 0, 0), (0, 1, 0)],
    'xz': [(0.0, -5.0, 0.0), (0, 0, 0), (0, 0, 1)],
    'yz': [(5.0,  0.0, 0.0), (0, 0, 0), (0, 0, 1)],
}

_VIEW_TITLES: dict[str, str] = {
    '3d': 'Vue 3D',
    'xy': 'Vue X-Y (depuis +Z)',
    'xz': 'Vue X-Z (depuis −Y)',
    'yz': 'Vue Y-Z (depuis +X)',
}


def export_cube_views(
    rotation: R,
    output_dir: str | Path = '.',
    views: list[str] | None = None,
    show_vertices: bool = True,
    show_edges: bool = True,
    show_faces: bool = True,
    size: float = 1.0,
    window_size: tuple[int, int] = (900, 700),
) -> list[Path]:
    """
    Export labeled cube views as PNG files (offscreen — no Qt required).

    Args:
        rotation:      scipy Rotation to apply to the cube and body-frame labels.
        output_dir:    Directory where PNG files are saved (created if needed).
        views:         View names to export. Default: ['3d', 'xy', 'xz', 'yz'].
        show_vertices: Label the 8 vertices (V_αβγ).
        show_edges:    Label the 12 edge midpoints (Eδ_σ₁σ₂).
        show_faces:    Label the 6 face centers (x_pos, …).
        size:          Cube side length (default 1.0).
        window_size:   Offscreen render resolution in pixels.

    Returns:
        List of Path objects pointing to the generated PNG files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    views = views or list(_CAMERA_POSITIONS.keys())
    euler = rotation.as_euler('XYZ', degrees=True)
    generated: list[Path] = []

    for view_name in views:
        p = pv.Plotter(off_screen=True, window_size=list(window_size))
        p.set_background('white')

        # Rotated cube
        cube = create_colored_cube(size=size)
        cube_rotated = apply_rotation_to_mesh(cube, rotation)
        p.add_mesh(cube_rotated, scalars='colors', rgb=True,
                   show_edges=True, edge_color='black', line_width=2)

        # Body-frame axes (rotate with cube)
        axis_len = 1.8 * size
        r_shaft = 0.02 * size
        for direction, color in [
            ((1, 0, 0), '#4DA6FF'),
            ((0, 1, 0), '#FFE633'),
            ((0, 0, 1), '#FF3333'),
        ]:
            d = np.array(direction, dtype=float)
            arrow = pv.Arrow(start=tuple(-d * axis_len / 2), direction=direction,
                             scale=axis_len, tip_radius=r_shaft,
                             tip_length=0.1, shaft_radius=r_shaft * 0.6)
            p.add_mesh(apply_rotation_to_mesh(arrow, rotation), color=color)

        # Lab-frame axes (fixed)
        lab_len = 1.2 * size
        lr = 0.02 * size
        for direction, color in [
            ((1, 0, 0), '#4DA6FF'),
            ((0, 1, 0), '#FFE633'),
            ((0, 0, 1), '#FF3333'),
        ]:
            p.add_mesh(pv.Arrow(start=(0, 0, 0), direction=direction,
                                scale=lab_len, tip_radius=lr,
                                tip_length=0.15, shaft_radius=lr * 0.6),
                       color=color)

        # Labels (body frame — rotated with cube)
        if show_faces:
            pts, lbs = get_face_label_data(size=size, rotation=rotation)
            p.add_point_labels(pts, lbs, font_size=14, text_color='black',
                               shape=None, always_visible=True, bold=True,
                               show_points=False)

        if show_edges:
            pts, lbs = get_edge_label_data(size=size, rotation=rotation)
            p.add_point_labels(pts, lbs, font_size=10, text_color='#444444',
                               shape=None, always_visible=True, show_points=False)

        if show_vertices:
            pts, lbs = get_vertex_label_data(size=size, rotation=rotation)
            p.add_point_labels(pts, lbs, font_size=10, text_color='#222222',
                               shape=None, always_visible=True, show_points=False)

        # Camera
        p.camera_position = _CAMERA_POSITIONS[view_name]
        p.camera.zoom(0.85)

        # Title
        p.add_text(
            f"{_VIEW_TITLES[view_name]}  —  "
            f"θx={euler[0]:.1f}°  θy={euler[1]:.1f}°  θz={euler[2]:.1f}°",
            position='upper_left', font_size=11, color='black')

        output_path = output_dir / f"cube_{view_name}.png"
        p.screenshot(str(output_path))
        p.close()
        generated.append(output_path)
        print(f"  Exported: {output_path}")

    return generated
