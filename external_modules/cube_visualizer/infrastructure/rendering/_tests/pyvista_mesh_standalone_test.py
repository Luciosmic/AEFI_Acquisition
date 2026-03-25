"""
Fenêtre PyVista manuelle (hors CI).

Pytest : test ignoré par défaut. Script : ``python pyvista_mesh_standalone_test.py`` depuis ce dossier
ou avec PYTHONPATH sur ``visualize_cube``.
"""
import sys
from pathlib import Path

import pytest

# Permet ``python path/to/pyvista_mesh_standalone_test.py`` sans installer le package
if __name__ == "__main__":
    _viz = Path(__file__).resolve().parents[3]
    if str(_viz) not in sys.path:
        sys.path.insert(0, str(_viz))

import pyvista as pv

from cube_visualizer.domain.sensor_rotation import rotation_from_euler_xyz
from cube_visualizer.infrastructure.rendering.cube_mesh_factory import (
    apply_rotation_to_mesh,
    create_colored_cube,
)


@pytest.mark.skip(reason="Fenêtre PyVista — exécution manuelle")
def test_standalone_pyvista_window_skipped():
    """Référence pour pytest ; ne s'exécute pas en CI."""
    _open_standalone_window()


def _open_standalone_window() -> None:
    plotter = pv.Plotter()
    plotter.set_background("white")
    plotter.show_grid()
    cube = create_colored_cube(size=1.0)
    rot = rotation_from_euler_xyz(15.0, 20.0, 30.0)
    cube_rotated = apply_rotation_to_mesh(cube.copy(), rot)
    if "colors" in cube_rotated.cell_data:
        plotter.add_mesh(
            cube_rotated,
            scalars="colors",
            rgb=True,
            show_edges=True,
            edge_color="black",
            line_width=2,
            opacity=1.0,
        )
    else:
        plotter.add_mesh(
            cube_rotated,
            color="lightgray",
            show_edges=True,
            edge_color="black",
            line_width=2,
            opacity=1.0,
        )
    plotter.show(auto_close=False, interactive_update=True)


if __name__ == "__main__":
    _open_standalone_window()
