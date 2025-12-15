import pyvista as pv
import numpy as np

# Créer un plotter PyVista
plotter = pv.Plotter()

# Créer un cube avec PyVista
cube = pv.Cube(x_length=1, y_length=1, z_length=1)

# Rotation du cube pour aligner sa grande diagonale avec l'axe vertical (z)
# La grande diagonale va du point (-0.5, -0.5, -0.5) au point (0.5, 0.5, 0.5)

# Méthode plus précise pour aligner la diagonale avec l'axe Z
diag_vector = np.array([1, 1, 1])
diag_vector = diag_vector / np.linalg.norm(diag_vector)  # Normaliser
z_axis = np.array([0, 0, 1])

# Calculer l'axe de rotation (produit vectoriel) et l'angle (produit scalaire)
rotation_axis = np.cross(diag_vector, z_axis)
rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)  # Normaliser
dot_product = np.dot(diag_vector, z_axis)
rotation_angle = np.arccos(dot_product) * 180 / np.pi  # Convertir en degrés

# Créer la transformation de rotation
transform = pv.transformations.axis_angle_rotation(rotation_axis, rotation_angle)

# Appliquer la rotation au cube
cube_transformed = cube.copy()
cube_transformed.transform(transform)

# Créer un plan de coupe horizontal (perpendiculaire à l'axe z)
# Le plan passe par le milieu de la grande diagonale (0, 0, 0)
plane = pv.Plane(center=(0, 0, 0), direction=(0, 0, 1), i_size=2, j_size=2)

# Couper le cube avec le plan
cube_slice = cube_transformed.slice(normal=(0, 0, 1), origin=(0, 0, 0))

# Ajouter le cube transformé avec transparence
plotter.add_mesh(cube_transformed, color='lightgray', style='surface', opacity=0.5, 
                 show_edges=True, line_width=2, edge_color='black')

# Ajouter la section de coupe
plotter.add_mesh(cube_slice, color='red', show_edges=True, line_width=3, edge_color='black')

# Ajouter le plan de coupe avec transparence
plotter.add_mesh(plane, color='lightblue', opacity=0.3)

# Ajouter une ligne représentant la grande diagonale
diagonal_line = pv.Line((-0.5, -0.5, -0.5), (0.5, 0.5, 0.5))
diagonal_line_transformed = diagonal_line.copy()
diagonal_line_transformed.transform(transform)
plotter.add_mesh(diagonal_line_transformed, color='white', line_width=5)

# Ajouter des points aux extrémités de la diagonale pour mieux visualiser
point1 = pv.Sphere(center=(-0.5, -0.5, -0.5), radius=0.03)
point2 = pv.Sphere(center=(0.5, 0.5, 0.5), radius=0.03)
point1_transformed = point1.copy()
point2_transformed = point2.copy()
point1_transformed.transform(transform)
point2_transformed.transform(transform)
plotter.add_mesh(point1_transformed, color='black')
plotter.add_mesh(point2_transformed, color='black')

# Ajouter des axes et une grille
plotter.add_axes()
plotter.show_grid()

# Ajouter un titre
plotter.add_title("Coupe d'un cube par un plan horizontal")

# Définir une position de caméra adaptée pour mieux voir la coupe
plotter.camera_position = [(2, -3, 2), (0, 0, 0), (0, 0, 1)]

# Afficher la visualisation
plotter.show()



