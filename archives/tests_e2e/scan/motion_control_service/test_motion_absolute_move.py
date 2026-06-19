"""
E2E Test: Motion Absolute Move

Tests absolute motion control through MotionControlService.
Validates: absolute move → position update → completion.
"""

import unittest
import time
from tests_e2e.base import (
    DiagramFriendlyTest,
    create_mock_motion_port,
    create_event_bus,
)
from application.services.motion_control_service.motion_control_service import MotionControlService
from domain.shared.value_objects.position_2d import Position2D


class TestMotionAbsoluteMove(DiagramFriendlyTest):
    """
    Test absolute motion control.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        self.motion_port = create_mock_motion_port(event_bus=self.event_bus, delay_ms=10.0)
        self.motion_service = MotionControlService(self.motion_port, self.event_bus)
    
    def test_absolute_move_nominal(self):
        """
        Test nominal absolute move operation.
        """
        self.log_divider("Execute Absolute Move")
        
        target_x, target_y = 15.0, 20.0
        self.log_interaction("Test", "CALL", "MotionService", f"move_absolute({target_x}, {target_y})")
        result = self.motion_service.move_absolute(target_x, target_y)
        
        self.log_interaction("Test", "ASSERT", "MotionService", "Move succeeded",
                           {"result": result.is_success}, expect=True, got=result.is_success)
        self.assertTrue(result.is_success, "Move should succeed")
        
        # Wait for motion to complete
        time.sleep(0.1)
        
        # Verify final position
        final_pos = self.motion_port.get_current_position()
        self.log_interaction("Test", "ASSERT", "MotionPort", "Final position correct",
                           {"expected": (target_x, target_y),
                            "got": (final_pos.x, final_pos.y)},
                           expect=(target_x, target_y),
                           got=(final_pos.x, final_pos.y))
        
        self.assertAlmostEqual(final_pos.x, target_x, places=2)
        self.assertAlmostEqual(final_pos.y, target_y, places=2)
    
    def test_absolute_move_single_axis(self):
        """
        Test absolute move on single axis (X or Y).
        """
        self.log_divider("Execute Single Axis Move")
        
        # Move to initial position
        self.motion_service.move_absolute(10.0, 10.0)
        time.sleep(0.1)
        
        # Move only X axis
        target_x = 25.0
        self.log_interaction("Test", "CALL", "MotionService", f"move_absolute_x({target_x})")
        result = self.motion_service.move_absolute_x(target_x)
        
        self.assertTrue(result.is_success)
        time.sleep(0.1)
        
        final_pos = self.motion_port.get_current_position()
        self.log_interaction("Test", "ASSERT", "MotionPort", "X position updated, Y unchanged",
                           {"x": final_pos.x, "y": final_pos.y},
                           expect=(target_x, 10.0), got=(final_pos.x, final_pos.y))
        
        self.assertAlmostEqual(final_pos.x, target_x, places=2)
        self.assertAlmostEqual(final_pos.y, 10.0, places=2)
        
        # Move only Y axis
        target_y = 30.0
        self.log_interaction("Test", "CALL", "MotionService", f"move_absolute_y({target_y})")
        result = self.motion_service.move_absolute_y(target_y)
        
        self.assertTrue(result.is_success)
        time.sleep(0.1)
        
        final_pos = self.motion_port.get_current_position()
        self.log_interaction("Test", "ASSERT", "MotionPort", "Y position updated, X unchanged",
                           {"x": final_pos.x, "y": final_pos.y},
                           expect=(target_x, target_y), got=(final_pos.x, final_pos.y))
        
        self.assertAlmostEqual(final_pos.x, target_x, places=2)
        self.assertAlmostEqual(final_pos.y, target_y, places=2)


if __name__ == '__main__':
    unittest.main()

