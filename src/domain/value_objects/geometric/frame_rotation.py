from dataclasses import dataclass, field
import math
from typing import Tuple, List
import numpy as np

@dataclass(frozen=True)
class FrameRotation:
    """Represents a 3D rotation defined by Euler angles (intrinsic XYZ convention).
    
    Uses quaternion mathematics to perform efficient and numerically stable
    3D vector rotations. The rotation is defined by three angles applied
    in the order: Rz * Ry * Rx.
    
    This value object is immutable and provides bidirectional rotation
    transformations between any two reference frames.
    """
    theta_x_deg: float
    theta_y_deg: float
    theta_z_deg: float
    
    # Quaternions are derived, so we exclude them from init and compute post-init
    # But since it's frozen, we compute them on demand or use a factory.
    # For simplicity in a Value Object, we can compute properties.
    
    @property
    def rotation_quaternion(self) -> np.ndarray:
        """Compute the forward rotation quaternion (Frame A -> Frame B)."""
        return self._compute_quaternion(self.theta_x_deg, self.theta_y_deg, self.theta_z_deg)

    @property
    def inverse_quaternion(self) -> np.ndarray:
        """Compute the inverse rotation quaternion (Frame B -> Frame A)."""
        q = self.rotation_quaternion
        # Conjugate for unit quaternion is inverse
        return np.array([q[0], -q[1], -q[2], -q[3]])

    @classmethod
    def default(cls) -> 'FrameRotation':
        """Create a default rotation configuration.
        
        Returns the standard rotation angles used in the experimental setup:
        - theta_x = -45° (rotation around X axis)
        - theta_y = arctan(1/√2) ≈ 35.26° (rotation around Y axis)
        - theta_z = 0° (no rotation around Z axis)
        """
        return cls(
            theta_x_deg=-45.0,
            theta_y_deg=math.degrees(math.atan(1 / math.sqrt(2))), # ~35.26
            theta_z_deg=0.0
        )

    def rotate_vector(self, x: float, y: float, z: float, to_bench_frame: bool = True) -> Tuple[float, float, float]:
        """Rotate a 3D vector using the defined rotation.
        
        Args:
            x, y, z: Components of the vector to rotate
            to_bench_frame: If True, applies inverse rotation (Frame B -> Frame A)
                          If False, applies forward rotation (Frame A -> Frame B)
        
        Returns:
            Tuple of rotated vector components (x', y', z')
        """
        v = np.array([x, y, z])
        q = self.inverse_quaternion if to_bench_frame else self.rotation_quaternion
        
        # Quaternion rotation: q * v * q_conj
        # 1. Convert vector to pure quaternion
        v_quat = np.array([0, v[0], v[1], v[2]])
        
        # 2. Multiply q * v_quat
        qv = self._quaternion_multiply(q, v_quat)
        
        # 3. Multiply result * q_conj
        q_conj = np.array([q[0], -q[1], -q[2], -q[3]])
        qv_rotated = self._quaternion_multiply(qv, q_conj)
        
        return (qv_rotated[1], qv_rotated[2], qv_rotated[3])

    def _compute_quaternion(self, tx: float, ty: float, tz: float) -> np.ndarray:
        """Compute the composite rotation quaternion from Euler angles.
        
        Applies rotations in the order: Z * Y * X (intrinsic rotations).
        Returns a normalized unit quaternion.
        """
        tx_rad = math.radians(tx)
        ty_rad = math.radians(ty)
        tz_rad = math.radians(tz)
        
        qx = np.array([math.cos(tx_rad/2), math.sin(tx_rad/2), 0, 0])
        qy = np.array([math.cos(ty_rad/2), 0, math.sin(ty_rad/2), 0])
        qz = np.array([math.cos(tz_rad/2), 0, 0, math.sin(tz_rad/2)])
        
        # Order: Z * Y * X
        q_temp = self._quaternion_multiply(qz, qy)
        q_final = self._quaternion_multiply(q_temp, qx)
        
        return q_final / np.linalg.norm(q_final)

    def _quaternion_multiply(self, q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
        """Multiply two quaternions using Hamilton product.
        
        Quaternion format: [w, x, y, z] where w is the scalar part.
        """
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        
        w = w1*w2 - x1*x2 - y1*y2 - z1*z2
        x = w1*x2 + x1*w2 + y1*z2 - z1*y2
        y = w1*y2 - x1*z2 + y1*w2 + z1*x2
        z = w1*z2 + x1*y2 - y1*x2 + z1*w2
        
        return np.array([w, x, y, z])
