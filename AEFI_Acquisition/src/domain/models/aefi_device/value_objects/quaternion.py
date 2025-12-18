from dataclasses import dataclass
import math
from domain.shared.value_objects.vector_3d import Vector3D

@dataclass(frozen=True)
class Quaternion:
    """
    Immutable representation of a Quaternion (w + xi + yj + zk) for 3D rotations.
    """
    w: float
    x: float
    y: float
    z: float

    @staticmethod
    def from_euler(roll: float, pitch: float, yaw: float) -> 'Quaternion':
        """
        Create a Quaternion from Euler angles (in radians).
        Order: Roll (X) -> Pitch (Y) -> Yaw (Z)
        """
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy

        return Quaternion(w, x, y, z)

    def inverse(self) -> 'Quaternion':
        """Returns the conjugate (inverse for unit quaternions)."""
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def rotate(self, vector: Vector3D) -> Vector3D:
        """
        Rotate a 3D vector using this quaternion.
        v' = q * v * q^-1
        """
        # Convert vector to pure quaternion (0, vx, vy, vz)
        # We optimize the multiplication here instead of implementing full Quaternion mul
        
        # t = 2 * cross(q_xyz, v)
        # v_prime = v + q_w * t + cross(q_xyz, t)
        
        # q vector part
        qx, qy, qz = self.x, self.y, self.z
        
        # Cross product q x v
        tx = 2.0 * (qy * vector.z - qz * vector.y)
        ty = 2.0 * (qz * vector.x - qx * vector.z)
        tz = 2.0 * (qx * vector.y - qy * vector.x)
        
        # Cross product q x t
        txx = (qy * tz - qz * ty)
        tyy = (qz * tx - qx * tz)
        tzz = (qx * ty - qy * tx)
        
        # v' = v + w*t + t_cross
        new_x = vector.x + self.w * tx + txx
        new_y = vector.y + self.w * ty + tyy
        new_z = vector.z + self.w * tz + tzz
        
        return Vector3D(new_x, new_y, new_z)
