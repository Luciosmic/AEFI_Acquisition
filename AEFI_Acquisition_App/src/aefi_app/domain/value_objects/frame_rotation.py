from dataclasses import dataclass, field
import math
from typing import Tuple, List
import numpy as np

@dataclass(frozen=True)
class FrameRotation:
    """Represents the rotation between the Bench Frame and the Sensor Frame.
    
    Handles the quaternion mathematics to transform measurements from the
    sensor's local frame (Probe) to the absolute bench frame.
    
    Transformation: E_probe = Rz * Ry * Rx * E_bench
    """
    theta_x_deg: float
    theta_y_deg: float
    theta_z_deg: float
    
    # Quaternions are derived, so we exclude them from init and compute post-init
    # But since it's frozen, we compute them on demand or use a factory.
    # For simplicity in a Value Object, we can compute properties.
    
    @property
    def rotation_quaternion(self) -> np.ndarray:
        """Compute the rotation quaternion (Bench -> Probe)."""
        return self._compute_quaternion(self.theta_x_deg, self.theta_y_deg, self.theta_z_deg)

    @property
    def inverse_quaternion(self) -> np.ndarray:
        """Compute the inverse quaternion (Probe -> Bench)."""
        q = self.rotation_quaternion
        # Conjugate for unit quaternion is inverse
        return np.array([q[0], -q[1], -q[2], -q[3]])

    @classmethod
    def default(cls) -> 'FrameRotation':
        """Create the standard configuration for the 4SphereSquared setup."""
        # Standard angles from legacy code
        return cls(
            theta_x_deg=-45.0,
            theta_y_deg=math.degrees(math.atan(1 / math.sqrt(2))), # ~35.26
            theta_z_deg=0.0
        )

    def rotate_vector(self, x: float, y: float, z: float, to_bench_frame: bool = True) -> Tuple[float, float, float]:
        """Rotate a 3D vector."""
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
        """Helper to compute composite quaternion."""
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
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        
        w = w1*w2 - x1*x2 - y1*y2 - z1*z2
        x = w1*x2 + x1*w2 + y1*z2 - z1*y2
        y = w1*y2 - x1*z2 + y1*w2 + z1*x2
        z = w1*z2 + x1*y2 - y1*x2 + z1*w2
        
        return np.array([w, x, y, z])
