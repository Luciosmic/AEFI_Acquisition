import pyvista as pv
import numpy as np

# Créer un plotter PyVista
plotter = pv.Plotter()

# Créer un cube avec PyVista
cube = pv.Cube(x_length=2, y_length=1.5, z_length=1)

# Définir des couleurs différentes pour chaque face
# Créer un tableau de couleurs pour chaque face (6 faces)
face_colors = np.array([
    [1, 0, 0],  # Rouge
    [0, 1, 0],  # Vert
    [0, 0, 1],  # Bleu
    [1, 1, 0],  # Jaune
    [1, 0, 1],  # Magenta
    [0, 1, 1],  # Cyan
])

# Appliquer les couleurs aux faces
cube.cell_data["colors"] = face_colors
cube.cell_data.set_active("colors")

# Ajouter le cube au plotter
plotter.add_mesh(cube, show_edges=True, line_width=3, edge_color='black')

# Ajouter des axes pour une meilleure orientation
plotter.add_axes(labels_off=False)

# Ajouter un titre
plotter.add_title("Cube 3D avec faces colorées", font_size=18)

# Définir une position de caméra
plotter.camera_position = [(4, 3, 2), (0, 0, 0), (0, 0, 1)]

# Afficher le cube
plotter.show()
