import unittest
from unittest.mock import MagicMock
from application.services.motion_control_service.motion_control_service import MotionControlService
from application.services.motion_control_service.i_motion_port import IMotionPort
from domain.value_objects.geometric.position_2d import Position2D
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from tool.diagram_friendly_test import DiagramFriendlyTest


class TestMotionControlService(DiagramFriendlyTest):

    def setUp(self):
        super().setUp()
        self.motion_port = MagicMock(spec=IMotionPort)
        self.motion_port.get_current_position.return_value = Position2D(0.0, 0.0)
        self.motion_port.get_axis_limits.return_value = (200.0, 200.0)
        self.event_bus = InMemoryEventBus()
        self.service = MotionControlService(
            motion_port=self.motion_port,
            event_bus=self.event_bus,
        )

    def test_move_relative_calls_port(self):
        result = self.service.move_relative(10.0, 5.0)
        self.assertTrue(result.is_success)
        self.motion_port.move_to.assert_called_once()

    def test_emergency_stop_publishes_event(self):
        events = []
        self.event_bus.subscribe("emergencystoptriggered", events.append)
        self.service.emergency_stop()
        self.assertEqual(len(events), 1)


if __name__ == "__main__":
    unittest.main()
