import pyvista as pv
import numpy as np

# Créer un plotter PyVista
plotter = pv.Plotter()

# Créer un cube avec PyVista
cube = pv.Cube(x_length=1, y_length=1, z_length=1)

# Rotation du cube pour aligner sa grande diagonale avec l'axe vertical (z)
# La grande diagonale va du point (-0.5, -0.5, -0.5) au point (0.5, 0.5, 0.5)
# Nous devons effectuer une rotation pour aligner cette diagonale avec l'axe z

# Créer une matrice de transformation pour la rotation
transform = pv.transformations.axis_angle_rotation([1, 0, 0], 45)
transform2 = pv.transformations.axis_angle_rotation([0, 1, 0], 35.264)  # arctan(1/sqrt(2)) ≈ 35.264°

# Appliquer les transformations pour aligner la diagonale avec l'axe z
cube_transformed = cube.copy()
cube_transformed.transform(transform)
cube_transformed.transform(transform2)

# Pas de couleurs spécifiques pour les faces

# Créer un plan de coupe horizontal (perpendiculaire à l'axe z)
# Le plan passe par le milieu de la grande diagonale (0, 0, 0)
plane = pv.Plane(center=(0, 0, 0), direction=(0, 0, 1), i_size=2, j_size=2)

# Couper le cube avec le plan
cube_slice = cube_transformed.slice(normal=(0, 0, 1), origin=(0, 0, 0))

# Ajouter le cube transformé avec transparence
plotter.add_mesh(cube_transformed, color='lightgray', style='surface', opacity=1, show_edges=True, line_width=2, edge_color='black')

# Ajouter la section de coupe
plotter.add_mesh(cube_slice, color='red', show_edges=True, line_width=3, edge_color='black')

# Ajouter le plan de coupe avec transparence
plotter.add_mesh(plane, color='lightblue', opacity=0.3)

# Ajouter des axes et une grille
plotter.add_axes()
plotter.show_grid()

# Ajouter un titre
plotter.add_title("Coupe d'un cube par un plan horizontal")

# Définir une position de caméra adaptée pour mieux voir la coupe
plotter.camera_position = [(2, -3, 2), (0, 0, 0), (0, 0, 1)]

# Désactiver la perspective isométrique en utilisant une projection parallèle (orthographique)
plotter.enable_parallel_projection()

# Afficher la visualisation
plotter.show()
