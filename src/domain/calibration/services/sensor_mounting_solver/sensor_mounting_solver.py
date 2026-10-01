"""
Sensor Mounting Solver

See sensor_mounting_solver_intention.md.
"""

import numpy as np
from scipy.spatial.transform import Rotation

from domain.calibration.errors.sensor_response_degenerate_error import SensorResponseDegenerateError
from domain.calibration.value_objects.sensor_mounting_fit.sensor_mounting_fit import SensorMountingFit
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import SensorRotationAngles

# ponytail: tuning knob, not physics — below this, P is set by noise.
MIN_RESPONSE_SEPARATION_DEGREES = 45.0

_TARGETS_SOURCES = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])  # X_DIR -> +e_x, Y_DIR -> +e_y


def _angle_degrees(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.degrees(np.arccos(np.clip(np.dot(a, b), -1.0, 1.0))))


def solve_mounting_angles(response_x_sensor, response_y_sensor) -> SensorMountingFit:
    """Mounting angles P bringing the sensor responses to X and Y excitation
    (sensor frame) onto +e_x and +e_y of the sources frame (Wahba, least squares)."""
    responses = []
    for name, response in (("X", response_x_sensor), ("Y", response_y_sensor)):
        response = np.asarray(response, dtype=float)
        norm = np.linalg.norm(response)
        if not norm > 0.0:
            raise SensorResponseDegenerateError(f"Réponse du capteur nulle sous excitation {name}")
        responses.append(response / norm)
    u_x, u_y = responses

    separation = _angle_degrees(u_x, u_y)
    if not MIN_RESPONSE_SEPARATION_DEGREES <= separation <= 180.0 - MIN_RESPONSE_SEPARATION_DEGREES:
        raise SensorResponseDegenerateError(
            f"Réponses X et Y séparées de {separation:.1f}° (attendu ~90°, minimum "
            f"{MIN_RESPONSE_SEPARATION_DEGREES:.0f}°) : le montage n'est pas déterminé"
        )

    rotation, _ = Rotation.align_vectors(_TARGETS_SOURCES, np.array([u_x, u_y]))
    p = rotation.as_matrix()
    return SensorMountingFit(
        angles=SensorRotationAngles.from_mounting_matrix(p),
        misalignment_x_degrees=_angle_degrees(p @ u_x, _TARGETS_SOURCES[0]),
        misalignment_y_degrees=_angle_degrees(p @ u_y, _TARGETS_SOURCES[1]),
        response_separation_degrees=separation,
    )
