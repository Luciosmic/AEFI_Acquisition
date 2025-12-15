"""
Géométrie et mathématiques pour la visualisation du cube sensor.

Responsabilité : Calculs de rotation, création de géométrie, transformations.
"""
import numpy as np
import pyvista as pv
from scipy.spatial.transform import Rotation as R
import math


def create_colored_cube(size=1.0):
    """
    Crée un cube avec les faces colorées selon les axes.
    
    Convention de couleurs (alignée avec les axes _labo à rotation 0°) :
    - X = Bleu (pour se superposer à X_labo bleu)
    - Y = Jaune (pour se superposer à Y_labo jaune)
    - Z = Rouge (pour se superposer à Z_labo rouge)
    
    Args:
        size: Taille du cube (défaut: 1.0)
    
    Returns:
        pv.PolyData: Cube avec couleurs assignées aux faces
    """
    cube = pv.Cube(x_length=size, y_length=size, z_length=size, center=(0, 0, 0))
    
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
    n_cells = cube.n_cells
    if n_cells == 6:
        cube.cell_data["colors"] = colors
    else:
        cube.cell_data["colors"] = colors[:n_cells]
    
    return cube


def apply_rotation_to_mesh(mesh, rotation: R):
    """
    Applique une rotation à un mesh PyVista.
    
    Args:
        mesh: Mesh PyVista à transformer
        rotation: Objet Rotation de scipy.spatial.transform
    
    Returns:
        pv.PolyData: Mesh transformé (copie)
    """
    mesh_copy = mesh.copy()
    points = mesh_copy.points
    points_rotated = rotation.apply(points)
    mesh_copy.points = points_rotated
    return mesh_copy


def create_rotation_from_euler_xyz(theta_x_deg, theta_y_deg, theta_z_deg):
    """
    Crée une rotation à partir d'angles d'Euler (ordre XYZ EXTRINSÈQUE).
    
    IMPORTANT: Utilise des rotations EXTRINSÈQUES (axes fixes du laboratoire).
    - Rotation autour de X du labo (fixe)
    - Puis autour de Y du labo (fixe)  
    - Puis autour de Z du labo (fixe)
    
    Args:
        theta_x_deg: Angle de rotation autour de X du labo (degrés)
        theta_y_deg: Angle de rotation autour de Y du labo (degrés)
        theta_z_deg: Angle de rotation autour de Z du labo (degrés)
    
    Returns:
        R: Objet Rotation de scipy.spatial.transform
    """
    # 'XYZ' (majuscules) = rotations extrinsèques (axes fixes du labo)
    # 'xyz' (minuscules) = rotations intrinsèques (axes du capteur) - INCORRECT
    return R.from_euler('XYZ', [theta_x_deg, theta_y_deg, theta_z_deg], degrees=True)


def get_default_theta_x():
    """Retourne l'angle X par défaut (~35.26°)."""
    return math.degrees(math.atan(1 / math.sqrt(2)))

def get_default_theta_y():
    """Retourne l'angle Y par défaut (45°)."""
    return 45.0
