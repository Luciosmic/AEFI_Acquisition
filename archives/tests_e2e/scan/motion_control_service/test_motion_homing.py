"""
E2E Test: Motion Homing

Tests homing operations through MotionControlService.
Validates: homing X, Y, both axes → position reset.
"""

import unittest
import time
from tests_e2e.base import (
    DiagramFriendlyTest,
    create_mock_motion_port,
    create_event_bus,
)
from application.services.motion_control_service.motion_control_service import MotionControlService


class TestMotionHoming(DiagramFriendlyTest):
    """
    Test homing operations.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        self.motion_port = create_mock_motion_port(event_bus=self.event_bus, delay_ms=10.0)
        self.motion_service = MotionControlService(self.motion_port, self.event_bus)
    
    def test_home_x_axis(self):
        """
        Test homing X axis only.
        """
        self.log_divider("Execute Home X")
        
        # Move to a known position first
        self.motion_service.move_absolute(10.0, 5.0)
        time.sleep(0.1)
        
        # Home X axis
        self.log_interaction("Test", "CALL", "MotionService", "home_x()")
        result = self.motion_service.home_x()
        
        self.log_interaction("Test", "ASSERT", "MotionService", "Home succeeded",
                           {"result": result.is_success}, expect=True, got=result.is_success)
        self.assertTrue(result.is_success, "Home X should succeed")
        
        time.sleep(0.1)
        
        # Verify X is at 0, Y unchanged
        final_pos = self.motion_port.get_current_position()
        self.log_interaction("Test", "ASSERT", "MotionPort", "X homed to 0, Y unchanged",
                           {"x": final_pos.x, "y": final_pos.y},
                           expect=(0.0, 5.0), got=(final_pos.x, final_pos.y))
        
        self.assertAlmostEqual(final_pos.x, 0.0, places=2)
        self.assertAlmostEqual(final_pos.y, 5.0, places=2)
    
    def test_home_y_axis(self):
        """
        Test homing Y axis only.
        """
        self.log_divider("Execute Home Y")
        
        # Move to a known position first
        self.motion_service.move_absolute(10.0, 5.0)
        time.sleep(0.1)
        
        # Home Y axis
        self.log_interaction("Test", "CALL", "MotionService", "home_y()")
        result = self.motion_service.home_y()
        
        self.assertTrue(result.is_success)
        time.sleep(0.1)
        
        # Verify Y is at 0, X unchanged
        final_pos = self.motion_port.get_current_position()
        self.log_interaction("Test", "ASSERT", "MotionPort", "Y homed to 0, X unchanged",
                           {"x": final_pos.x, "y": final_pos.y},
                           expect=(10.0, 0.0), got=(final_pos.x, final_pos.y))
        
        self.assertAlmostEqual(final_pos.x, 10.0, places=2)
        self.assertAlmostEqual(final_pos.y, 0.0, places=2)
    
    def test_home_both_axes(self):
        """
        Test homing both axes.
        """
        self.log_divider("Execute Home XY")
        
        # Move to a known position first
        self.motion_service.move_absolute(15.0, 20.0)
        time.sleep(0.1)
        
        # Home both axes
        self.log_interaction("Test", "CALL", "MotionService", "home_xy()")
        result = self.motion_service.home_xy()
        
        self.log_interaction("Test", "ASSERT", "MotionService", "Home succeeded",
                           {"result": result.is_success}, expect=True, got=result.is_success)
        self.assertTrue(result.is_success, "Home XY should succeed")
        
        time.sleep(0.1)
        
        # Verify both axes at 0
        final_pos = self.motion_port.get_current_position()
        self.log_interaction("Test", "ASSERT", "MotionPort", "Both axes homed to 0",
                           {"x": final_pos.x, "y": final_pos.y},
                           expect=(0.0, 0.0), got=(final_pos.x, final_pos.y))
        
        self.assertAlmostEqual(final_pos.x, 0.0, places=2)
        self.assertAlmostEqual(final_pos.y, 0.0, places=2)


if __name__ == '__main__':
    unittest.main()

