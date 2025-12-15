import pyvista as pv
import numpy as np

# Fonction principale qui sera appelée lors du clic sur les boutons
def update_vector_field(direction):
    # Effacer le plotter actuel
    plotter.clear()
    
    # Ajouter le cube
    plotter.add_mesh(cube, color='lightgray', style='surface', opacity=0.7, 
                    show_edges=True, line_width=2, edge_color='black')
    
    # Créer un champ de vecteurs uniforme selon la direction choisie
    if direction == 'x':
        vectors = np.zeros_like(points)
        vectors[:, 0] = 1.0  # Direction X
        plotter.add_text("Champ de vecteurs selon X", position=(0.05, 0.05), 
                        font_size=14, color='black')
    elif direction == 'y':
        vectors = np.zeros_like(points)
        vectors[:, 1] = 1.0  # Direction Y
        plotter.add_text("Champ de vecteurs selon Y", position=(0.05, 0.05), 
                        font_size=14, color='black')
    
    # Ajouter le champ de vecteurs
    plotter.add_arrows(points, vectors, mag=0.3, color='red')
    
    # Ajouter des axes et une grille
    plotter.add_axes()
    plotter.show_grid()
    
    # Mettre à jour le rendu
    plotter.update()

# Créer un plotter interactif
plotter = pv.Plotter()

# Créer un cube
cube = pv.Cube(x_length=1, y_length=1, z_length=1)

# Créer une grille de points pour le champ de vecteurs
x, y, z = np.meshgrid(
    np.linspace(-0.7, 0.7, 5),
    np.linspace(-0.7, 0.7, 5),
    np.linspace(-0.7, 0.7, 5)
)
points = np.column_stack((x.flatten(), y.flatten(), z.flatten()))

# Créer une fonction de rappel pour le bouton
def toggle_direction(state):
    if state:
        update_vector_field('y')  # Direction Y quand activé
    else:
        update_vector_field('x')  # Direction X quand désactivé

# Ajouter un bouton pour changer la direction du champ de vecteurs
plotter.add_checkbox_button_widget(
    toggle_direction, value=False, 
    position=(10, 40), size=30, 
    border_size=1, color_on='red', color_off='grey'
)

# Ajouter un texte explicatif pour le bouton
plotter.add_text("Cliquer pour changer la direction (X/Y)", position=(0.05, 0.95), 
                font_size=12, color='black')

# Initialiser avec des vecteurs selon X
update_vector_field('x')

# Ajouter un titre
plotter.add_title("Cube avec champ de vecteurs uniforme")

# Afficher la visualisation
plotter.show()
