"""
SensorToEFSourcesFrameRotator - Rotates vectors from the sensor frame to the EF sources frame.

Convention (reference: src/domain/calibration/value_objects/rotation_convention/rotation_convention_intention.md):
the angles (theta_x, theta_y, theta_z) define the mounting rotation
P = Rx(theta_x)·Ry(theta_y)·Rz(theta_z) (extrinsic, fixed sources axes, Z then Y then X,
scipy 'XYZ'), which brings the sensor, aligned on the sources frame, to its mounting.
The measurement is E_sensor = Pᵀ·E_sources; the rotator applies E_sources = P·E_sensor.
Uses quaternion-based rotation for numerical stability.
"""

from typing import Tuple, Optional
import numpy as np
from scipy.spatial.transform import Rotation as R


class SensorToEFSourcesFrameRotator:
    """
    Applies E_sources = P·E_sensor (sensor frame -> EF sources frame), where P is the
    mounting rotation Rx·Ry·Rz (extrinsic, scipy 'XYZ') defined by the angles.
    Uses quaternion representation for numerical stability and to avoid gimbal lock.
    """
    
    def __init__(self):
        """Initialize frame rotator with identity rotation."""
        self.rotation_angles = (0.0, 0.0, 0.0)  # degrees
        self.rotation = R.identity()
        self.quaternion = self.rotation.as_quat()  # [x, y, z, w]
    
    def set_rotation_angles(self, theta_x: float, theta_y: float, theta_z: float):
        """
        Set the angles (degrees) of the mounting rotation P = Rx·Ry·Rz
        (extrinsic, Z then Y then X, scipy 'XYZ'). The stored rotation is P
        (sensor -> sources): E_sources = P·E_sensor.

        Args:
            theta_x: theta_x of P (degrees)
            theta_y: theta_y of P (degrees)
            theta_z: theta_z of P (degrees)
        """
        self.rotation_angles = (theta_x, theta_y, theta_z)
        self.rotation = R.from_euler('XYZ', [theta_x, theta_y, theta_z], degrees=True)
        self.quaternion = self.rotation.as_quat()
    
    def create_quaternion(self, angles: Tuple[float, float, float]) -> np.ndarray:
        """
        Create the quaternion of the applied rotation P (sensor -> sources).

        Args:
            angles: Tuple of (theta_x, theta_y, theta_z) in degrees of the
                    mounting rotation P = Rx·Ry·Rz (extrinsic, scipy 'XYZ')

        Returns:
            Quaternion as [x, y, z, w]
        """
        return R.from_euler('XYZ', angles, degrees=True).as_quat()
    
    def apply_rotation_to_vector(self, vector: np.ndarray) -> np.ndarray:
        """
        Apply rotation to a single 3D vector.
        
        Args:
            vector: 3D vector, shape (3,)
            
        Returns:
            Rotated vector, shape (3,)
        """
        return self.rotation.apply(vector)
    
    def rotate_vector_field(self, data: np.ndarray) -> np.ndarray:
        """
        Apply rotation to entire vector field.
        
        Args:
            data: Vector field data, shape (H, W, 6) where channels are
                  [Ux_I, Ux_Q, Uy_I, Uy_Q, Uz_I, Uz_Q]
                  
        Returns:
            Rotated vector field, same shape as input
        """
        h, w, c = data.shape
        
        if c != 6:
            raise ValueError(f"Expected 6 channels (3 axes × I,Q), got {c}")
        
        # Reshape to (H*W, 6)
        flat_data = data.reshape(-1, 6)
        
        # Separate I and Q components
        # For each pixel, we have a complex vector: V = (Ux + iUx', Uy + iUy', Uz + iUz')
        # We rotate the real part (I components) and imaginary part (Q components) separately
        
        i_components = flat_data[:, [0, 2, 4]]  # Ux_I, Uy_I, Uz_I
        q_components = flat_data[:, [1, 3, 5]]  # Ux_Q, Uy_Q, Uz_Q
        
        # Apply rotation to I and Q components
        i_rotated = self.rotation.apply(i_components)
        q_rotated = self.rotation.apply(q_components)
        
        # Reconstruct the data
        rotated_flat = np.zeros_like(flat_data)
        rotated_flat[:, [0, 2, 4]] = i_rotated
        rotated_flat[:, [1, 3, 5]] = q_rotated
        
        # Reshape back to original shape
        rotated = rotated_flat.reshape(h, w, c)
        
        return rotated
    
    def get_rotation_matrix(self) -> np.ndarray:
        """
        Get the rotation matrix representation.
        
        Returns:
            3×3 rotation matrix
        """
        return self.rotation.as_matrix()
    
    def get_quaternion(self) -> np.ndarray:
        """
        Get the quaternion representation.
        
        Returns:
            Quaternion as [x, y, z, w]
        """
        return self.quaternion
    
    def rotate(
        self, 
        data: np.ndarray, 
        angles: Optional[Tuple[float, float, float]] = None
    ) -> Tuple[np.ndarray, dict]:
        """
        Complete rotation pipeline.
        
        Args:
            data: Input vector field, shape (H, W, 6)
            angles: Optional (theta_x, theta_y, theta_z) in degrees of the
                   mounting rotation P. If None, uses current rotation.
                   
        Returns:
            Tuple of (rotated data, metadata dict)
        """
        if angles is not None:
            self.set_rotation_angles(*angles)
        
        rotated = self.rotate_vector_field(data)
        
        metadata = {
            'rotation_angles': self.rotation_angles,
            'quaternion': self.quaternion.tolist(),
            'rotation_matrix': self.get_rotation_matrix().tolist(),
            'convention': "P = Rx·Ry·Rz (scipy 'XYZ'), mounting sources->sensor; applied E_sources = P·E_sensor"
        }
        
        return rotated, metadata
