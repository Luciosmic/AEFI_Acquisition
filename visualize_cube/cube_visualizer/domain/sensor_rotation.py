"""
Sensor rotation math — Domain layer.

Responsibility: Pure quaternion mathematics. No PyVista, no Qt.
These functions are the canonical source of truth for sensor orientation
calculations and can be reused by any layer (including the main application).
"""
import numpy as np
from scipy.spatial.transform import Rotation as R, Slerp
import math


# ===== EULER / QUATERNION CONVERSIONS =====

def quaternion_from_euler_xyz(theta_x_deg: float, theta_y_deg: float, theta_z_deg: float) -> np.ndarray:
    """
    Convert Euler angles to a quaternion (EXTRINSIC — lab-fixed axes).

    Args:
        theta_x_deg: Rotation around lab X (degrees)
        theta_y_deg: Rotation around lab Y (degrees)
        theta_z_deg: Rotation around lab Z (degrees)

    Returns:
        np.ndarray: Quaternion [x, y, z, w] (scipy convention)
    """
    # 'XYZ' (uppercase) = extrinsic rotations (fixed lab axes)
    rot = R.from_euler('XYZ', [theta_x_deg, theta_y_deg, theta_z_deg], degrees=True)
    return rot.as_quat()


def euler_xyz_from_quaternion(quat: np.ndarray) -> tuple:
    """
    Convert a quaternion back to Euler angles (EXTRINSIC XYZ order).

    Args:
        quat: Quaternion [x, y, z, w] (scipy convention)

    Returns:
        tuple: (theta_x_deg, theta_y_deg, theta_z_deg) in degrees
    """
    rot = R.from_quat(quat)
    euler = rot.as_euler('XYZ', degrees=True)
    return tuple(euler)


def rotation_from_euler_xyz(theta_x_deg: float, theta_y_deg: float, theta_z_deg: float) -> R:
    """
    Create a scipy Rotation from Euler angles (EXTRINSIC XYZ).

    Args:
        theta_x_deg: Rotation around lab X (degrees)
        theta_y_deg: Rotation around lab Y (degrees)
        theta_z_deg: Rotation around lab Z (degrees)

    Returns:
        R: scipy Rotation object
    """
    return R.from_euler('XYZ', [theta_x_deg, theta_y_deg, theta_z_deg], degrees=True)


def rotation_from_quaternion(quat: np.ndarray) -> R:
    """
    Create a scipy Rotation from a quaternion.

    Args:
        quat: Quaternion [x, y, z, w]

    Returns:
        R: scipy Rotation object
    """
    return R.from_quat(quat)


# ===== QUATERNION OPERATIONS =====

def quaternion_identity() -> np.ndarray:
    """Return the identity quaternion (no rotation). Returns [0, 0, 0, 1]."""
    return np.array([0.0, 0.0, 0.0, 1.0])


def quaternion_multiply(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """
    Compose two rotations via quaternion multiplication.

    Args:
        q1: First quaternion [x, y, z, w]
        q2: Second quaternion [x, y, z, w]

    Returns:
        np.ndarray: Resulting quaternion [x, y, z, w]
    """
    return (R.from_quat(q1) * R.from_quat(q2)).as_quat()


def quaternion_slerp(q1: np.ndarray, q2: np.ndarray, t: float) -> np.ndarray:
    """
    Spherical Linear Interpolation (SLERP) between two quaternions.

    Args:
        q1: Start quaternion [x, y, z, w]
        q2: End quaternion [x, y, z, w]
        t: Interpolation parameter [0, 1]

    Returns:
        np.ndarray: Interpolated quaternion [x, y, z, w]
    """
    key_rots = R.from_quat([q1, q2])
    slerp = Slerp([0, 1], key_rots)
    return slerp([t])[0].as_quat()


# ===== DEFAULTS =====

def get_default_theta_x() -> float:
    """Default sensor X angle (~35.26°)."""
    return math.degrees(math.atan(1 / math.sqrt(2)))


def get_default_theta_y() -> float:
    """Default sensor Y angle (45°)."""
    return 45.0


def get_default_quaternion() -> np.ndarray:
    """
    Default quaternion for the sensor cube orientation.

    Equivalent to: theta_x=~35.26°, theta_y=45°, theta_z=0°

    Returns:
        np.ndarray: Quaternion [x, y, z, w]
    """
    return quaternion_from_euler_xyz(get_default_theta_x(), get_default_theta_y(), 0.0)
