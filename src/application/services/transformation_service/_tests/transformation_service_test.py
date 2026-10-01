import math
import unittest

import numpy as np

from application.services.transformation_service.transformation_service import TransformationService
from application.services.transformation_service.dtos.transformation_dtos import SetRotationAnglesDTO
from application.services.sensor_calibration_service.sensor_calibration_service import (
    ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC,
)
from domain.calibration.events.active_sensor_rotation_changed.active_sensor_rotation_changed import (
    ActiveSensorRotationChanged,
)
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from tool.diagram_friendly_test import DiagramFriendlyTest


class TestTransformationService(DiagramFriendlyTest):

    def setUp(self):
        super().setUp()
        self.service = TransformationService()

    def test_identity_when_disabled(self):
        self.service.set_enabled(False)
        vector = (1.0, 0.0, 0.0)
        result = self.service.transform_sensor_to_source(vector)
        self.assertEqual(result, vector)

    def test_enabled_applies_rotation(self):
        self.service.set_rotation_angles(SetRotationAnglesDTO(theta_x=0.0, theta_y=0.0, theta_z=90.0))
        self.service.set_enabled(True)
        x, y, z = self.service.transform_sensor_to_source((1.0, 0.0, 0.0))
        self.assertAlmostEqual(x, 0.0, places=5)
        self.assertAlmostEqual(y, 1.0, places=5)
        self.assertAlmostEqual(z, 0.0, places=5)

    def test_follows_active_sensor_rotation_changed(self):
        event_bus = InMemoryEventBus()
        service = TransformationService(event_bus)

        event_bus.publish(
            ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC,
            ActiveSensorRotationChanged(
                angles=SensorRotationAngles(theta_x_degrees=1.0, theta_y_degrees=2.0, theta_z_degrees=3.0),
                is_calibrated=True,
                recorded_at=None,
            ),
        )

        self.assertEqual(service.get_rotation_angles(), (1.0, 2.0, 3.0))


def _rx(deg):
    a = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def _ry(deg):
    b = math.radians(deg)
    return np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])


def _rz(deg):
    c = math.radians(deg)
    return np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])


class TestRotationConventionGuard(unittest.TestCase):
    """Freezes the convention documented in
    domain/calibration/value_objects/rotation_convention/rotation_convention_intention.md:
    P = Rx(theta_x)·Ry(theta_y)·Rz(theta_z) is the mounting rotation (fixed sources
    axes, applied Z then Y then X); measurement E_sensor = Pᵀ·E_sources;
    coordinate transform E_sources = P·E_sensor."""

    def _service(self, theta_x, theta_y, theta_z) -> TransformationService:
        service = TransformationService()
        service.set_rotation_angles(SetRotationAnglesDTO(theta_x=theta_x, theta_y=theta_y, theta_z=theta_z))
        service.set_enabled(True)
        return service

    def _sensor_to_source_matrix(self, theta_x, theta_y, theta_z) -> np.ndarray:
        service = self._service(theta_x, theta_y, theta_z)
        columns = [service.transform_sensor_to_source(tuple(e)) for e in np.eye(3)]
        return np.array(columns).T

    def test_sensor_to_source_matrix_is_rx_ry_rz(self):
        tx, ty, tz = 10.0, 20.0, 30.0
        expected = _rx(tx) @ _ry(ty) @ _rz(tz)

        np.testing.assert_allclose(self._sensor_to_source_matrix(tx, ty, tz), expected, atol=1e-12)

    def test_ideal_angles_put_sources_vertical_on_a_cube_diagonal(self):
        """The cube diagonal (-1, 1, 1)/sqrt(3) of the sensor frame is e_z^sources:
        P·(-1, 1, 1)/sqrt(3) = (0, 0, 1)."""
        service = self._service(math.degrees(math.atan(1 / math.sqrt(2))), 45.0, 0.0)

        diagonal_in_sources = service.transform_sensor_to_source(
            tuple(np.array([-1.0, 1.0, 1.0]) / math.sqrt(3))
        )

        np.testing.assert_allclose(diagonal_in_sources, np.array([0.0, 0.0, 1.0]), atol=1e-9)

    def test_negated_angles_are_not_the_transpose(self):
        """Transposing P is not negating its angles: Pᵀ = Rz(-tz)·Ry(-ty)·Rx(-tx),
        whereas P(-theta) = Rx(-tx)·Ry(-ty)·Rz(-tz)."""
        tx, ty, tz = 10.0, 20.0, 30.0
        p = self._sensor_to_source_matrix(tx, ty, tz)
        p_negated = self._sensor_to_source_matrix(-tx, -ty, -tz)

        np.testing.assert_allclose(p.T, _rz(-tz) @ _ry(-ty) @ _rx(-tx), atol=1e-12)
        self.assertFalse(np.allclose(p_negated, p.T, atol=1e-6))


if __name__ == "__main__":
    unittest.main()
