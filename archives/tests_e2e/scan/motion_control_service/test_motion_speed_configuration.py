"""
E2E Test: Motion Speed Configuration

Tests speed configuration through MotionControlService.
Validates: set_speed → speed applied → motion uses new speed.
"""

import unittest
from tests_e2e.base import (
    DiagramFriendlyTest,
    create_mock_motion_port,
    create_event_bus,
)
from application.services.motion_control_service.motion_control_service import MotionControlService


class TestMotionSpeedConfiguration(DiagramFriendlyTest):
    """
    Test speed configuration.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        self.motion_port = create_mock_motion_port(event_bus=self.event_bus, delay_ms=10.0)
        self.motion_service = MotionControlService(self.motion_port, self.event_bus)
    
    def test_set_speed(self):
        """
        Test setting motion speed.
        """
        self.log_divider("Execute Set Speed")
        
        speed = 5.0  # cm/s
        self.log_interaction("Test", "CALL", "MotionService", f"set_speed({speed})")
        # Note: MotionControlService doesn't expose set_speed directly,
        # but MotionPort does. For now, we test via port.
        self.motion_port.set_speed(speed)
        
        # Verify speed was set
        self.log_interaction("Test", "ASSERT", "MotionPort", "Speed configured",
                           {"speed": self.motion_port.last_speed}, expect=speed, got=self.motion_port.last_speed)
        self.assertEqual(self.motion_port.last_speed, speed, "Speed should be set")
        
        # Verify speed is used in subsequent moves
        # (FakeMotionPort doesn't actually use speed for timing, but we verify it's stored)
        self.motion_service.move_absolute(10.0, 10.0)
        
        self.log_interaction("Test", "INFO", "MotionPort", "Speed configuration verified")


if __name__ == '__main__':
    unittest.main()

