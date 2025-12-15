"""
Géométrie et mathématiques pour la visualisation du cube sensor.

Responsabilité : Calculs de rotation, création de géométrie, transformations.
Version améliorée utilisant les quaternions pour plus de stabilité.
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
    colors = np.array([
        [0.3, 0.6, 1.0],   # +X : Bleu
        [0.3, 0.6, 1.0],   # -X : Bleu
        [1.0, 0.9, 0.2],   # +Y : Jaune
        [1.0, 0.9, 0.2],   # -Y : Jaune
        [1.0, 0.2, 0.2],   # +Z : Rouge
        [1.0, 0.2, 0.2],   # -Z : Rouge
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


# ===== QUATERNION-BASED ROTATION FUNCTIONS =====

def create_rotation_from_quaternion(quat):
    """
    Crée une rotation à partir d'un quaternion.
    
    Args:
        quat: Quaternion [x, y, z, w] (scipy convention)
    
    Returns:
        R: Objet Rotation de scipy.spatial.transform
    """
    return R.from_quat(quat)


def create_rotation_from_euler_xyz(theta_x_deg, theta_y_deg, theta_z_deg):
    """
    Crée une rotation à partir d'angles d'Euler (ordre XYZ).
    
    DEPRECATED: Préférer quaternion_from_euler_xyz() pour plus de stabilité.
    
    Args:
        theta_x_deg: Angle de rotation autour de X (degrés)
        theta_y_deg: Angle de rotation autour de Y (degrés)
        theta_z_deg: Angle de rotation autour de Z (degrés)
    
    Returns:
        R: Objet Rotation de scipy.spatial.transform
    """
    return R.from_euler('xyz', [theta_x_deg, theta_y_deg, theta_z_deg], degrees=True)


def quaternion_from_euler_xyz(theta_x_deg, theta_y_deg, theta_z_deg):
    """
    Convertit des angles d'Euler en quaternion (EXTRINSÈQUE - axes fixes du labo).
    
    IMPORTANT: Utilise des rotations EXTRINSÈQUES (axes fixes du laboratoire).
    
    Args:
        theta_x_deg: Angle de rotation autour de X du labo (degrés)
        theta_y_deg: Angle de rotation autour de Y du labo (degrés)
        theta_z_deg: Angle de rotation autour de Z du labo (degrés)
    
    Returns:
        np.ndarray: Quaternion [x, y, z, w] (scipy convention)
    """
    # 'XYZ' (majuscules) = rotations extrinsèques (axes fixes)
    rot = R.from_euler('XYZ', [theta_x_deg, theta_y_deg, theta_z_deg], degrees=True)
    return rot.as_quat()  # Returns [x, y, z, w]


def euler_xyz_from_quaternion(quat):
    """
    Convertit un quaternion en angles d'Euler (ordre XYZ EXTRINSÈQUE).
    
    Args:
        quat: Quaternion [x, y, z, w] (scipy convention)
    
    Returns:
        tuple: (theta_x_deg, theta_y_deg, theta_z_deg) en degrés (axes fixes du labo)
    """
    rot = R.from_quat(quat)
    # 'XYZ' (majuscules) = rotations extrinsèques
    euler = rot.as_euler('XYZ', degrees=True)
    return tuple(euler)


def quaternion_multiply(q1, q2):
    """
    Multiplie deux quaternions (composition de rotations).
    
    Args:
        q1: Premier quaternion [x, y, z, w]
        q2: Second quaternion [x, y, z, w]
    
    Returns:
        np.ndarray: Quaternion résultant [x, y, z, w]
    """
    r1 = R.from_quat(q1)
    r2 = R.from_quat(q2)
    r_result = r1 * r2
    return r_result.as_quat()


def quaternion_slerp(q1, q2, t):
    """
    Interpolation sphérique entre deux quaternions (SLERP).
    
    Utile pour des animations fluides.
    
    Args:
        q1: Quaternion de départ [x, y, z, w]
        q2: Quaternion d'arrivée [x, y, z, w]
        t: Paramètre d'interpolation [0, 1]
    
    Returns:
        np.ndarray: Quaternion interpolé [x, y, z, w]
    """
    from scipy.spatial.transform import Slerp
    
    key_rots = R.from_quat([q1, q2])
    key_times = [0, 1]
    slerp = Slerp(key_times, key_rots)
    
    return slerp([t])[0].as_quat()


def quaternion_identity():
    """
    Retourne le quaternion identité (pas de rotation).
    
    Returns:
        np.ndarray: [0, 0, 0, 1]
    """
    return np.array([0.0, 0.0, 0.0, 1.0])


def get_default_theta_y():
    """Retourne l'angle Y par défaut (~35.26°)."""
    return math.degrees(math.atan(1 / math.sqrt(2)))


def get_default_quaternion():
    """
    Retourne le quaternion par défaut pour la rotation du cube.
    
    Équivalent à: theta_x=0, theta_y=~35.26°, theta_z=0
    
    Returns:
        np.ndarray: Quaternion [x, y, z, w]
    """
    return quaternion_from_euler_xyz(0.0, get_default_theta_y(), 0.0)
