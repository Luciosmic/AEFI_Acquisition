"""
Visualisation du cube sensor avec rotation physique et couleurs des axes.

Le cube représente le sensor physique avec :
- X_mes (bleu) : axe X du sensor
- Y_mes (jaune) : axe Y du sensor  
- Z_mes (rouge) : axe Z du sensor

Les faces du cube sont colorées selon leur orientation par rapport aux axes.
La rotation physique du sensor est appliquée pour montrer l'orientation réelle.
"""
import pyvista as pv
import numpy as np
from scipy.spatial.transform import Rotation as R
import math

def create_colored_cube(size=1.0):
    """
    Crée un cube avec les faces colorées selon les axes.
    
    Convention de couleurs (alignée avec les axes _labo à rotation 0°) :
    - X = Bleu (pour se superposer à X_labo bleu)
    - Y = Jaune (pour se superposer à Y_labo jaune)
    - Z = Rouge (pour se superposer à Z_labo rouge)
    
    Les faces sont colorées selon leur normale :
    - Face +X (normale vers +X) = Bleu
    - Face -X (normale vers -X) = Bleu (même couleur)
    - Face +Y (normale vers +Y) = Jaune
    - Face -Y (normale vers -Y) = Jaune (même couleur)
    - Face +Z (normale vers +Z) = Rouge
    - Face -Z (normale vers -Z) = Rouge (même couleur)
    """
    # Créer un cube unitaire centré à l'origine
    cube = pv.Cube(x_length=size, y_length=size, z_length=size, center=(0, 0, 0))
    
    # Obtenir les normales des faces pour déterminer leur orientation
    # PyVista organise les faces dans un ordre spécifique
    # Pour un cube : [0: +X, 1: -X, 2: +Y, 3: -Y, 4: +Z, 5: -Z]
    n_cells = cube.n_cells
    
    # Couleurs pour chaque face selon l'axe (format RGB [0-1])
    # Faces opposées ont la même couleur
    # À rotation 0° : X_mes (bleu) aligné avec X_labo (bleu), Y_mes (jaune) avec Y_labo (jaune), Z_mes (rouge) avec Z_labo (rouge)
    colors = np.array([
        [0.3, 0.6, 1.0],   # +X : Bleu (pour X_mes → X_labo)
        [0.3, 0.6, 1.0],   # -X : Bleu (même que +X)
        [1.0, 0.9, 0.2],   # +Y : Jaune (pour Y_mes → Y_labo)
        [1.0, 0.9, 0.2],   # -Y : Jaune (même que +Y)
        [1.0, 0.2, 0.2],   # +Z : Rouge (pour Z_mes → Z_labo)
        [1.0, 0.2, 0.2],   # -Z : Rouge (même que +Z)
    ])
    
    # Assigner les couleurs aux cellules (faces)
    # PyVista attend un tableau de forme (n_cells, 3) pour RGB
    if n_cells == 6:
        cube.cell_data["colors"] = colors
    else:
        # Si le nombre de cellules est différent, utiliser les premières couleurs
        cube.cell_data["colors"] = colors[:n_cells]
    
    return cube

def apply_rotation_to_mesh(mesh, rotation: R):
    """
    Applique une rotation 3D à un mesh PyVista.
    
    Args:
        mesh: Mesh PyVista
        rotation: Rotation scipy (Rotation object)
    """
    # Obtenir les points du mesh
    points = mesh.points
    
    # Appliquer la rotation (rotation autour de l'origine)
    points_rotated = rotation.apply(points)
    
    # Mettre à jour les points du mesh
    mesh.points = points_rotated
    
    return mesh

def visualize_sensor_cube(
    theta_x_deg: float = 0.0,
    theta_y_deg: float = None,
    theta_z_deg: float = 0.0,
    show_labo_frame: bool = True,
    show_mes_frame: bool = True
):
    """
    Visualise le cube sensor avec rotation physique.
    
    Args:
        theta_x_deg: Rotation autour de X en degrés (défaut: -45°)
        theta_y_deg: Rotation autour de Y en degrés (défaut: ~35.26°)
        theta_z_deg: Rotation autour de Z en degrés (défaut: 0°)
        show_labo_frame: Afficher le repère global (labo)
        show_mes_frame: Afficher le repère local (mes)
    """
    # Calculer theta_y par défaut si non fourni
    if theta_y_deg is None:
        theta_y_deg = math.degrees(math.atan(1 / math.sqrt(2)))  # ~35.26°
    
    # Créer la rotation (ordre xyz, extrinsic)
    rotation = R.from_euler('xyz', [theta_x_deg, theta_y_deg, theta_z_deg], degrees=True)
    
    # Créer le plotter
    print("  Création du plotter...")
    plotter = pv.Plotter()
    plotter.set_background('white')
    print("  Plotter créé")
    
    # Créer le cube coloré
    cube = create_colored_cube(size=1.0)
    
    # Appliquer la rotation au cube
    cube_rotated = apply_rotation_to_mesh(cube.copy(), rotation)
    
    # Ajouter le cube au plotter avec les couleurs des faces
    # Vérifier si les couleurs sont définies
    if "colors" in cube_rotated.cell_data:
        plotter.add_mesh(
            cube_rotated,
            scalars="colors",
            rgb=True,
            show_edges=True,
            edge_color='black',
            line_width=2,
            opacity=1.0  # Cube non transparent
        )
    else:
        # Fallback : cube gris si pas de couleurs
        plotter.add_mesh(
            cube_rotated,
            color='lightgray',
            show_edges=True,
            edge_color='black',
            line_width=2,
            opacity=1.0  # Cube non transparent
        )
    
    # Ajouter les axes du repère local (mes) - au centre du cube
    if show_mes_frame:
        axis_length = 0.8
        arrow_radius = 0.05
        
        # X_mes (Bleu) - à rotation 0° aligné avec X_labo (bleu)
        arrow_x = pv.Arrow(
            start=(0, 0, 0),
            direction=(1, 0, 0),
            scale=axis_length,
            tip_radius=arrow_radius,
            tip_length=0.2,
            shaft_radius=arrow_radius * 0.6
        )
        arrow_x_rotated = apply_rotation_to_mesh(arrow_x, rotation)
        plotter.add_mesh(arrow_x_rotated, color='#4DA6FF', label='X_mes')
        
        # Y_mes (Jaune) - à rotation 0° aligné avec Y_labo (jaune)
        arrow_y = pv.Arrow(
            start=(0, 0, 0),
            direction=(0, 1, 0),
            scale=axis_length,
            tip_radius=arrow_radius,
            tip_length=0.2,
            shaft_radius=arrow_radius * 0.6
        )
        arrow_y_rotated = apply_rotation_to_mesh(arrow_y, rotation)
        plotter.add_mesh(arrow_y_rotated, color='#FFE633', label='Y_mes')
        
        # Z_mes (Rouge) - à rotation 0° aligné avec Z_labo (rouge)
        arrow_z = pv.Arrow(
            start=(0, 0, 0),
            direction=(0, 0, 1),
            scale=axis_length,
            tip_radius=arrow_radius,
            tip_length=0.2,
            shaft_radius=arrow_radius * 0.6
        )
        arrow_z_rotated = apply_rotation_to_mesh(arrow_z, rotation)
        plotter.add_mesh(arrow_z_rotated, color='#FF3333', label='Z_mes')
    
    # Ajouter les axes du repère global (labo) - plus grands, en blanc
    if show_labo_frame:
        labo_axis_length = 1.5
        labo_arrow_radius = 0.03
        
        # X_labo (Bleu) - axe fixe du référentiel labo
        arrow_x_labo = pv.Arrow(
            start=(0, 0, 0),
            direction=(1, 0, 0),
            scale=labo_axis_length,
            tip_radius=labo_arrow_radius,
            tip_length=0.15,
            shaft_radius=labo_arrow_radius * 0.6
        )
        plotter.add_mesh(arrow_x_labo, color='#4DA6FF', line_width=3, label='X_labo')
        
        # Y_labo (Jaune) - axe fixe du référentiel labo
        arrow_y_labo = pv.Arrow(
            start=(0, 0, 0),
            direction=(0, 1, 0),
            scale=labo_axis_length,
            tip_radius=labo_arrow_radius,
            tip_length=0.15,
            shaft_radius=labo_arrow_radius * 0.6
        )
        plotter.add_mesh(arrow_y_labo, color='#FFE633', line_width=3, label='Y_labo')
        
        # Z_labo (Rouge) - axe fixe du référentiel labo
        arrow_z_labo = pv.Arrow(
            start=(0, 0, 0),
            direction=(0, 0, 1),
            scale=labo_axis_length,
            tip_radius=labo_arrow_radius,
            tip_length=0.15,
            shaft_radius=labo_arrow_radius * 0.6
        )
        plotter.add_mesh(arrow_z_labo, color='#FF3333', line_width=3, label='Z_labo')
    
    # Ajouter une grille pour référence
    plotter.show_grid()
    
    # Ajouter des labels textuels
    plotter.add_text(
        f"Rotation: X={theta_x_deg:.1f}°, Y={theta_y_deg:.1f}°, Z={theta_z_deg:.1f}°",
        position='upper_left',
        font_size=12,
        color='black'
    )
    
    plotter.add_text(
        "X_mes (bleu) | Y_mes (jaune) | Z_mes (rouge)",
        position='upper_right',
        font_size=11,
        color='black'
    )
    
    # Ajouter un titre
    plotter.add_title("Cube Sensor - Orientation Physique", font_size=16, color='black')
    
    # Position de caméra pour une bonne vue
    plotter.camera_position = [
        (3, -3, 2),  # Position de la caméra
        (0, 0, 0),   # Point de focus
        (0, 0, 1)    # Vecteur up
    ]
    
    # Afficher
    print("  Ouverture de la fenêtre...")
    plotter.show()
    print("  Fenêtre fermée")

if __name__ == "__main__":
    print("=== Démarrage de la visualisation ===")
    print("Import des modules...")
    import sys
    print(f"Python: {sys.version}")
    print(f"PyVista version: {pv.__version__}")
    
    # Utiliser la rotation par défaut du cube (comme dans main_v2.py)
    print("Création de la visualisation...")
    try:
        visualize_sensor_cube(
            theta_x_deg=-45.0,
            theta_y_deg=None,  # Sera calculé automatiquement (~35.26°)
            theta_z_deg=0.0,
            show_labo_frame=True,
            show_mes_frame=True
        )
        print("Visualisation terminée.")
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()

