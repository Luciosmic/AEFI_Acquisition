"""
Test simple pour vérifier si PyVista fonctionne en fenêtre séparée.

Si ce test fonctionne, le problème vient de l'intégration Qt.
Si ce test ne fonctionne pas, le problème vient de PyVista lui-même.
"""
import sys
import pyvista as pv
from cube_geometry import create_colored_cube, apply_rotation_to_mesh, create_rotation_from_euler_xyz

def test_standalone():
    """Test PyVista en fenêtre séparée (sans Qt)."""
    print("Création d'un plotter PyVista standalone...")
    plotter = pv.Plotter()
    plotter.set_background('white')
    plotter.show_grid()
    
    print("Création du cube...")
    cube = create_colored_cube(size=1.0)
    
    print("Ajout du cube au plotter...")
    if "colors" in cube.cell_data:
        plotter.add_mesh(
            cube,
            scalars="colors",
            rgb=True,
            show_edges=True,
            edge_color='black',
            line_width=2,
            opacity=1.0
        )
    else:
        plotter.add_mesh(
            cube,
            color='lightgray',
            show_edges=True,
            edge_color='black',
            line_width=2,
            opacity=1.0
        )
    
    print("Rendu du plotter...")
    plotter.show(auto_close=False, interactive_update=True)
    print("Fenêtre PyVista ouverte. Fermez-la pour terminer le test.")

if __name__ == "__main__":
    test_standalone()

