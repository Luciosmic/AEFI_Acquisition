import pyvista as pv
import numpy as np

# Créer un plotter PyVista
plotter = pv.Plotter()

# Créer un cube avec PyVista
cube = pv.Cube()

# Ajouter le cube au plotter avec une couleur et de la transparence
plotter.add_mesh(cube, show_edges=True, line_width=2, color='lightblue', opacity=0.5)

# Ajouter des axes pour une meilleure orientation
plotter.add_axes()

# Ajouter une grille pour mieux visualiser l'espace 3D
plotter.show_grid()

# Ajouter un titre
plotter.add_title("Visualisation d'un cube 3D")

# Afficher le cube
plotter.show()
