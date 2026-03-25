"""Tests CubeVisualizerAdapter (réaction aux événements EventBus)."""
import sys
import unittest
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication

from cube_visualizer.infrastructure.messaging.event_bus import EventBus, Event, EventType
from cube_visualizer.infrastructure.rendering.cube_visualizer_adapter_pyvista import (
    CubeVisualizerAdapter,
)


class TestCubeVisualizerAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        self.event_bus = EventBus()

        def _skip_plotter_init(self):
            self.plotter = None
            self.plotter_widget = None

        with patch.object(CubeVisualizerAdapter, "_create_plotter_standalone", _skip_plotter_init):
            self.adapter = CubeVisualizerAdapter(event_bus=self.event_bus, parent_widget=None)
        self.adapter.update_view = Mock()
        self.adapter.reset_camera_view = Mock()

    def test_adapter_subscribes_to_same_event_bus(self):
        self.assertIs(self.adapter.event_bus, self.event_bus)

    def test_adapter_reacts_to_angles_changed_event(self):
        event = Event(
            event_type=EventType.ANGLES_CHANGED,
            data={"theta_x": 10.0, "theta_y": 20.0, "theta_z": 30.0},
        )
        self.event_bus.publish(event)
        QApplication.processEvents()
        self.adapter.update_view.assert_called_once()
        args = self.adapter.update_view.call_args[0]
        self.assertEqual(len(args), 1)

    def test_adapter_reacts_to_camera_view_changed_event(self):
        event = Event(
            event_type=EventType.CAMERA_VIEW_CHANGED,
            data={"view_name": "xy"},
        )
        self.event_bus.publish(event)
        QApplication.processEvents()
        self.adapter.reset_camera_view.assert_called_once_with("xy")


if __name__ == "__main__":
    unittest.main()
