"""Flux CommandBus → Presenter → EventBus (intégration légère)."""
import sys
import unittest

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
from cube_visualizer.domain.sensor_rotation import get_default_theta_x, get_default_theta_y
from cube_visualizer.infrastructure.messaging.command_bus import CommandBus, Command, CommandType
from cube_visualizer.infrastructure.messaging.event_bus import EventBus, EventType
from cube_visualizer.interface.cube_visualizer_presenter import CubeVisualizerPresenter


class FakeCubeVisualizerService(IApiCubeVisualizerService):
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


class TestCqrsFlow(unittest.TestCase):
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
        self.events_published = []

        def event_handler(event):
            self.events_published.append(event)

        self.event_bus.subscribe(EventType.ANGLES_CHANGED, event_handler)

    def test_full_flow_update_angles(self):
        self.command_bus.send(
            Command(CommandType.UPDATE_ANGLES, {"theta_x": 15.0, "theta_y": 25.0, "theta_z": 35.0})
        )
        for _ in range(5):
            QApplication.processEvents()

        theta_x, theta_y, theta_z = self.presenter.get_current_angles()
        self.assertEqual((theta_x, theta_y, theta_z), (15.0, 25.0, 35.0))
        self.assertEqual(len(self.events_published), 1)
        self.assertEqual(self.events_published[0].event_type, EventType.ANGLES_CHANGED)
        self.assertEqual(self.events_published[0].data["theta_x"], 15.0)

    def test_full_flow_reset(self):
        self.command_bus.send(
            Command(CommandType.UPDATE_ANGLES, {"theta_x": 45.0, "theta_y": 60.0, "theta_z": 90.0})
        )
        QApplication.processEvents()
        self.events_published.clear()

        self.command_bus.send(Command(CommandType.RESET_TO_DEFAULT, {}))
        QApplication.processEvents()

        self.assertEqual(len(self.events_published), 1)
        self.assertEqual(self.events_published[0].event_type, EventType.ANGLES_CHANGED)

    def test_multiple_commands_sequence(self):
        for tx, ty, tz in [(10.0, 20.0, 30.0), (40.0, 50.0, 60.0), (70.0, 80.0, 90.0)]:
            self.command_bus.send(
                Command(CommandType.UPDATE_ANGLES, {"theta_x": tx, "theta_y": ty, "theta_z": tz})
            )
            for _ in range(5):
                QApplication.processEvents()

        self.assertEqual(self.presenter.get_current_angles(), (70.0, 80.0, 90.0))
        self.assertEqual(len(self.events_published), 3)


if __name__ == "__main__":
    unittest.main()
