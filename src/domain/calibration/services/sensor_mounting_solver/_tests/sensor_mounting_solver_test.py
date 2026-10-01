import unittest

import numpy as np

from domain.calibration.errors.sensor_response_degenerate_error import SensorResponseDegenerateError
from domain.calibration.services.sensor_mounting_solver.sensor_mounting_solver import solve_mounting_angles
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import SensorRotationAngles

E_X = np.array([1.0, 0.0, 0.0])
E_Y = np.array([0.0, 1.0, 0.0])


def sensor_reading(true_angles: SensorRotationAngles, field_sources: np.ndarray) -> np.ndarray:
    """What a sensor mounted with P reads of a field: E_sensor = Pᵀ·E_sources."""
    return true_angles.mounting_matrix().T @ field_sources


def rotated_about_z(vector: np.ndarray, degrees: float) -> np.ndarray:
    return SensorRotationAngles(0.0, 0.0, degrees).mounting_matrix() @ vector


class TestSensorMountingSolver(unittest.TestCase):
    def test_recovers_the_mounting_angles_from_ideal_responses(self):
        true_angles = SensorRotationAngles(36.1, 44.2, 1.3)
        fit = solve_mounting_angles(sensor_reading(true_angles, E_X), sensor_reading(true_angles, E_Y))
        self.assertAlmostEqual(fit.angles.theta_x_degrees, 36.1)
        self.assertAlmostEqual(fit.angles.theta_y_degrees, 44.2)
        self.assertAlmostEqual(fit.angles.theta_z_degrees, 1.3)
        self.assertAlmostEqual(fit.misalignment_x_degrees, 0.0, places=6)
        self.assertAlmostEqual(fit.misalignment_y_degrees, 0.0, places=6)
        self.assertAlmostEqual(fit.response_separation_degrees, 90.0)

    def test_corrected_responses_land_on_the_sources_axes(self):
        """The criterion of the manual procedure: P·r_X along +x, P·r_Y along +y."""
        true_angles = SensorRotationAngles(-12.0, 20.0, 75.0)
        r_x, r_y = sensor_reading(true_angles, E_X), sensor_reading(true_angles, E_Y)
        p = solve_mounting_angles(r_x, r_y).angles.mounting_matrix()
        np.testing.assert_allclose(p @ r_x, E_X, atol=1e-9)
        np.testing.assert_allclose(p @ r_y, E_Y, atol=1e-9)

    def test_amplitude_does_not_change_the_angles(self):
        true_angles = SensorRotationAngles(35.3, 45.0, 0.0)
        fit = solve_mounting_angles(
            0.003 * sensor_reading(true_angles, E_X), 250.0 * sensor_reading(true_angles, E_Y)
        )
        self.assertAlmostEqual(fit.angles.theta_x_degrees, 35.3)
        self.assertAlmostEqual(fit.angles.theta_y_degrees, 45.0)
        self.assertAlmostEqual(fit.angles.theta_z_degrees, 0.0)

    def test_non_orthogonal_responses_share_the_misalignment(self):
        """Asymmetric sphere mounting: X field 4° off its axis, Y field on it.
        The fit splits the 4° between both instead of dumping it on one."""
        true_angles = SensorRotationAngles(35.3, 45.0, 0.0)
        fit = solve_mounting_angles(
            sensor_reading(true_angles, rotated_about_z(E_X, 4.0)), sensor_reading(true_angles, E_Y)
        )
        self.assertAlmostEqual(fit.response_separation_degrees, 86.0)
        self.assertAlmostEqual(fit.misalignment_x_degrees, 2.0, places=6)
        self.assertAlmostEqual(fit.misalignment_y_degrees, 2.0, places=6)

    def test_zero_response_is_refused(self):
        with self.assertRaises(SensorResponseDegenerateError):
            solve_mounting_angles(np.zeros(3), E_Y)

    def test_nearly_collinear_responses_are_refused(self):
        with self.assertRaises(SensorResponseDegenerateError):
            solve_mounting_angles(E_X, rotated_about_z(E_X, 10.0))

    def test_opposite_responses_are_refused(self):
        with self.assertRaises(SensorResponseDegenerateError):
            solve_mounting_angles(E_X, -E_X)


if __name__ == "__main__":
    unittest.main()
