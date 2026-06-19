from typing import Tuple
import numpy as np
from scipy.spatial.transform import Rotation as R


class CoordinateTransformer:
    def __init__(self) -> None:
        self._angles = np.array([0.0, 0.0, 0.0])
        self._rotation = R.identity()

    def set_rotation_angles(self, theta_x: float, theta_y: float, theta_z: float) -> None:
        self._angles = np.array([theta_x, theta_y, theta_z])
        self._rotation = R.from_euler('XYZ', self._angles, degrees=True)

    def sensor_to_source(self, v: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return tuple(self._rotation.apply(np.array(v)))

    def source_to_sensor(self, v: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return tuple(self._rotation.inv().apply(np.array(v)))
