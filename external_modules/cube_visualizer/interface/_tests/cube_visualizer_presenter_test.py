"""Tests pour CubeVisualizerPresenter (CommandBus + EventBus + service)."""
import sys
import unittest

import numpy as np
from PySide6.QtWidgets import QApplication

from cube_visualizer.application.cube_visualizer_service.dtos.sensor_orientation_dto import (
    SensorOrientationDto,
)
from cube_visualizer.application.cube_visualizer_service.dtos.update_angles_request_dto import (
    UpdateAnglesRequestDto,
)
from cube_visualizer.application.cube_visualizer_service.i_api_cube_visualizer_service import (
    IApiCubeVisualizerService,
)
from cube_visualizer.domain.sensor_rotation import (
    get_default_theta_x,
    get_default_theta_y,
    rotation_from_euler_xyz,
)
from cube_visualizer.infrastructure.messaging.command_bus import CommandBus, Command, CommandType
from cube_visualizer.infrastructure.messaging.event_bus import EventBus, EventType
from cube_visualizer.interface.cube_visualizer_presenter import CubeVisualizerPresenter


class FakeCubeVisualizerService(IApiCubeVisualizerService):
    """Double de test : état orientation + rendu no-op."""

    def __init__(self):
        self._theta_x = get_default_theta_x()
        self._theta_y = get_default_theta_y()
        self._theta_z = 0.0

    def update_angles(self, request: UpdateAnglesRequestDto) -> SensorOrientationDto:
        self._theta_x = request.theta_x
        self._theta_y = request.theta_y
        self._theta_z = request.theta_z
        return self.get_current_orientation()

    def reset_to_default(self) -> SensorOrientationDto:
        self._theta_x = get_default_theta_x()
        self._theta_y = get_default_theta_y()
        self._theta_z = 0.0
        return self.get_current_orientation()

    def get_current_orientation(self) -> SensorOrientationDto:
        return SensorOrientationDto(self._theta_x, self._theta_y, self._theta_z)


class TestCubeVisualizerPresenter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        self.command_bus = CommandBus()
        self.event_bus = EventBus()
        self.service = FakeCubeVisualizerService()
        self.presenter = CubeVisualizerPresenter(
            service=self.service,
            command_bus=self.command_bus,
            event_bus=self.event_bus,
        )
        self.received_events = []

        def event_handler(event):
            self.received_events.append(event)

        self.event_bus.subscribe(EventType.ANGLES_CHANGED, event_handler)

    def test_update_angles_via_command(self):
        cmd = Command(
            CommandType.UPDATE_ANGLES,
            {"theta_x": 10.0, "theta_y": 20.0, "theta_z": 30.0},
        )
        self.command_bus.send(cmd)
        for _ in range(5):
            QApplication.processEvents()

        theta_x, theta_y, theta_z = self.presenter.get_current_angles()
        self.assertEqual(theta_x, 10.0)
        self.assertEqual(theta_y, 20.0)
        self.assertEqual(theta_z, 30.0)

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].event_type, EventType.ANGLES_CHANGED)
        self.assertEqual(self.received_events[0].data["theta_x"], 10.0)
        self.assertEqual(self.received_events[0].data["theta_y"], 20.0)
        self.assertEqual(self.received_events[0].data["theta_z"], 30.0)

    def test_reset_to_default_via_command(self):
        cmd1 = Command(
            CommandType.UPDATE_ANGLES,
            {"theta_x": 45.0, "theta_y": 60.0, "theta_z": 90.0},
        )
        self.command_bus.send(cmd1)
        QApplication.processEvents()
        self.received_events.clear()

        cmd2 = Command(CommandType.RESET_TO_DEFAULT, {})
        self.command_bus.send(cmd2)
        QApplication.processEvents()

        theta_x, theta_y, theta_z = self.presenter.get_current_angles()
        self.assertAlmostEqual(theta_x, get_default_theta_x(), places=5)
        self.assertAlmostEqual(theta_y, get_default_theta_y(), places=5)
        self.assertEqual(theta_z, 0.0)

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].event_type, EventType.ANGLES_CHANGED)

    def test_get_current_angles_reflects_service(self):
        cmd = Command(
            CommandType.UPDATE_ANGLES,
            {"theta_x": 90.0, "theta_y": 0.0, "theta_z": 0.0},
        )
        self.command_bus.send(cmd)
        QApplication.processEvents()

        tx, ty, tz = self.presenter.get_current_angles()
        self.assertEqual((tx, ty, tz), (90.0, 0.0, 0.0))
        rot = rotation_from_euler_xyz(tx, ty, tz)
        vector = np.array([1, 0, 0])
        rotated = rot.apply(vector)
        np.testing.assert_array_almost_equal(rotated, [1, 0, 0], decimal=5)

    def test_multiple_commands(self):
        self.command_bus.send(
            Command(CommandType.UPDATE_ANGLES, {"theta_x": 10.0, "theta_y": 20.0, "theta_z": 30.0})
        )
        for _ in range(5):
            QApplication.processEvents()
        self.command_bus.send(
            Command(CommandType.UPDATE_ANGLES, {"theta_x": 40.0, "theta_y": 50.0, "theta_z": 60.0})
        )
        for _ in range(5):
            QApplication.processEvents()

        theta_x, theta_y, theta_z = self.presenter.get_current_angles()
        self.assertEqual(theta_x, 40.0)
        self.assertEqual(theta_y, 50.0)
        self.assertEqual(theta_z, 60.0)
        self.assertEqual(len(self.received_events), 2)


if __name__ == "__main__":
    unittest.main()
