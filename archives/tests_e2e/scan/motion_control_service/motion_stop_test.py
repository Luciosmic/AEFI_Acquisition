"""
E2E Test: Motion Stop

Tests stop operations (normal and emergency) through MotionControlService.
Validates: stop → motion interruption → proper state.
"""

import unittest
import time
from tests_e2e.base import (
    DiagramFriendlyTest,
    create_mock_motion_port,
    create_event_bus,
)
from application.services.motion_control_service.motion_control_service import MotionControlService


class TestMotionStop(DiagramFriendlyTest):
    """
    Test stop operations.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        # Use longer delay to allow stop during motion
        self.motion_port = create_mock_motion_port(event_bus=self.event_bus, delay_ms=100.0)
        self.motion_service = MotionControlService(self.motion_port, self.event_bus)
    
    def test_normal_stop(self):
        """
        Test normal stop (with deceleration).
        """
        self.log_divider("Execute Normal Stop")
        
        # Start a move
        self.log_interaction("Test", "CALL", "MotionService", "move_absolute(50.0, 50.0)")
        result = self.motion_service.move_absolute(50.0, 50.0)
        self.assertTrue(result.is_success)
        
        # Wait a bit for motion to start
        time.sleep(0.05)
        
        # Stop motion
        self.log_interaction("Test", "CALL", "MotionService", "stop()")
        result = self.motion_service.stop()
        
        self.log_interaction("Test", "ASSERT", "MotionService", "Stop succeeded",
                           {"result": result.is_success}, expect=True, got=result.is_success)
        self.assertTrue(result.is_success, "Stop should succeed")
        
        # Verify motion stopped
        time.sleep(0.1)
        is_moving = self.motion_port.is_moving()
        self.log_interaction("Test", "ASSERT", "MotionPort", "Motion stopped",
                           {"is_moving": is_moving}, expect=False, got=is_moving)
        self.assertFalse(is_moving, "Motion should be stopped")
    
    def test_emergency_stop(self):
        """
        Test emergency stop (immediate halt).
        """
        self.log_divider("Execute Emergency Stop")
        
        # Start a move
        self.log_interaction("Test", "CALL", "MotionService", "move_absolute(50.0, 50.0)")
        result = self.motion_service.move_absolute(50.0, 50.0)
        self.assertTrue(result.is_success)
        
        # Wait a bit for motion to start
        time.sleep(0.05)
        
        # Emergency stop
        self.log_interaction("Test", "CALL", "MotionService", "emergency_stop()")
        result = self.motion_service.emergency_stop()
        
        self.log_interaction("Test", "ASSERT", "MotionService", "Emergency stop succeeded",
                           {"result": result.is_success}, expect=True, got=result.is_success)
        self.assertTrue(result.is_success, "Emergency stop should succeed")
        
        # Verify motion stopped
        time.sleep(0.1)
        is_moving = self.motion_port.is_moving()
        self.log_interaction("Test", "ASSERT", "MotionPort", "Motion stopped",
                           {"is_moving": is_moving}, expect=False, got=is_moving)
        self.assertFalse(is_moving, "Motion should be stopped after emergency stop")


if __name__ == '__main__':
    unittest.main()

