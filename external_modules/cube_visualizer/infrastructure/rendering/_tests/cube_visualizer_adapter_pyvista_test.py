"""Tests CubeVisualizerAdapter (widget embarquable + réaction aux événements EventBus)."""
import os
import sys
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

from cube_visualizer.domain.sensor_rotation import rotation_from_euler_xyz
from cube_visualizer.infrastructure.messaging.event_bus import EventBus, Event, EventType
from cube_visualizer.infrastructure.rendering.cube_visualizer_adapter_pyvista import (
    CubeVisualizerAdapter,
)


class TestCubeVisualizerAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.event_bus = EventBus()
        self.adapter = CubeVisualizerAdapter(event_bus=self.event_bus)

    def tearDown(self):
        self.adapter.widget.close()

    def test_exposes_an_embeddable_widget_without_opening_a_window(self):
        self.assertIsInstance(self.adapter.widget, QWidget)
        QApplication.processEvents()
        self.assertFalse(self.adapter.widget.isVisible())

    def test_widget_is_parented_to_the_host(self):
        host = QWidget()
        adapter = CubeVisualizerAdapter(event_bus=EventBus(), parent_widget=host)
        self.assertIs(adapter.widget.parent(), host)
        adapter.widget.close()

    def test_update_view_draws_cube_and_both_axis_triads(self):
        self.adapter.update_view(rotation_from_euler_xyz(10.0, 20.0, 30.0))
        self.assertIsNotNone(self.adapter.cube_actor)
        self.assertIsNotNone(self.adapter.marker_actor)
        self.assertEqual(set(self.adapter.arrows_sensor), {"x", "y", "z"})
        self.assertEqual(set(self.adapter.arrows_sources), {"x", "y", "z"})

    def test_adapter_reacts_to_angles_changed_event(self):
        self.adapter.update_view = Mock()
        self.event_bus.publish(Event(
            event_type=EventType.ANGLES_CHANGED,
            data={"theta_x": 10.0, "theta_y": 20.0, "theta_z": 30.0},
        ))
        QApplication.processEvents()
        self.adapter.update_view.assert_called_once()

    def test_adapter_reacts_to_camera_view_changed_event(self):
        self.adapter.reset_camera_view = Mock()
        self.event_bus.publish(Event(
            event_type=EventType.CAMERA_VIEW_CHANGED, data={"view_name": "xy"},
        ))
        QApplication.processEvents()
        self.adapter.reset_camera_view.assert_called_once_with("xy")


if __name__ == "__main__":
    unittest.main()
