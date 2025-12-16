"""
Service de géométrie pour la visualisation du cube sensor.

Responsabilité : Calculs de rotation, transformations géométriques.
Pure domain logic - aucune dépendance sur PyVista, ModernGL, ou Qt.
"""
import math
from scipy.spatial.transform import Rotation as R


def create_rotation_from_euler_xyz(theta_x_deg: float, theta_y_deg: float, theta_z_deg: float) -> R:
    """
    Crée une rotation à partir d'angles d'Euler (ordre XYZ).
    
    Args:
        theta_x_deg: Angle de rotation autour de X (degrés)
        theta_y_deg: Angle de rotation autour de Y (degrés)
        theta_z_deg: Angle de rotation autour de Z (degrés)
    
    Returns:
        R: Objet Rotation de scipy.spatial.transform
    """
    return R.from_euler('xyz', [theta_x_deg, theta_y_deg, theta_z_deg], degrees=True)


def get_default_theta_y() -> float:
    """
    Retourne l'angle Y par défaut (~35.26°).
    
    Cet angle correspond à la rotation nécessaire pour aligner le cube
    dans une position standard.
    """
    return math.degrees(math.atan(1 / math.sqrt(2)))



