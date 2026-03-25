"""Tests unitaires pour EventBus."""
import sys
import unittest

from PySide6.QtWidgets import QApplication

from cube_visualizer.infrastructure.messaging.event_bus import EventBus, Event, EventType


class TestEventBus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        self.event_bus = EventBus()
        self.received_events = []

    def test_subscribe_and_publish_angles_changed(self):
        def handler(event: Event):
            self.received_events.append(event)

        self.event_bus.subscribe(EventType.ANGLES_CHANGED, handler)
        event = Event(
            event_type=EventType.ANGLES_CHANGED,
            data={"theta_x": 10.0, "theta_y": 20.0, "theta_z": 30.0},
        )
        self.event_bus.publish(event)
        QApplication.processEvents()

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].event_type, EventType.ANGLES_CHANGED)
        self.assertEqual(self.received_events[0].data["theta_x"], 10.0)
        self.assertEqual(self.received_events[0].data["theta_y"], 20.0)
        self.assertEqual(self.received_events[0].data["theta_z"], 30.0)

    def test_multiple_subscribers(self):
        subscriber1_events = []
        subscriber2_events = []

        def subscriber1(event: Event):
            subscriber1_events.append(event)

        def subscriber2(event: Event):
            subscriber2_events.append(event)

        self.event_bus.subscribe(EventType.ANGLES_CHANGED, subscriber1)
        self.event_bus.subscribe(EventType.ANGLES_CHANGED, subscriber2)
        event = Event(
            event_type=EventType.ANGLES_CHANGED,
            data={"theta_x": 1.0, "theta_y": 2.0, "theta_z": 3.0},
        )
        self.event_bus.publish(event)
        QApplication.processEvents()

        self.assertEqual(len(subscriber1_events), 1)
        self.assertEqual(len(subscriber2_events), 1)

    def test_unsubscribe(self):
        def handler(event: Event):
            self.received_events.append(event)

        self.event_bus.subscribe(EventType.ANGLES_CHANGED, handler)
        event = Event(
            event_type=EventType.ANGLES_CHANGED,
            data={"theta_x": 1.0, "theta_y": 2.0, "theta_z": 3.0},
        )
        self.event_bus.publish(event)
        QApplication.processEvents()
        self.assertEqual(len(self.received_events), 1)

        self.event_bus.unsubscribe(EventType.ANGLES_CHANGED, handler)
        self.received_events.clear()
        event = Event(
            event_type=EventType.ANGLES_CHANGED,
            data={"theta_x": 4.0, "theta_y": 5.0, "theta_z": 6.0},
        )
        self.event_bus.publish(event)
        QApplication.processEvents()
        self.assertEqual(len(self.received_events), 0)

    def test_camera_view_changed_event(self):
        def handler(event: Event):
            self.received_events.append(event)

        self.event_bus.subscribe(EventType.CAMERA_VIEW_CHANGED, handler)
        event = Event(
            event_type=EventType.CAMERA_VIEW_CHANGED,
            data={"view_name": "xy"},
        )
        self.event_bus.publish(event)
        QApplication.processEvents()

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].data["view_name"], "xy")


if __name__ == "__main__":
    unittest.main()
