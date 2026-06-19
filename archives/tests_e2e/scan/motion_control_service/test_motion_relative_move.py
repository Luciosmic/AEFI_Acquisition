"""
E2E Test: Motion Relative Move

Tests relative motion control through MotionControlService.
Validates: relative move → position update → completion.
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
from domain.shared.value_objects.operation_result import OperationResult


class TestMotionRelativeMove(DiagramFriendlyTest):
    """
    Test relative motion control.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        self.motion_port = create_mock_motion_port(event_bus=self.event_bus, delay_ms=10.0)
        self.motion_service = MotionControlService(self.motion_port, self.event_bus)
    
    def test_relative_move_nominal(self):
        """
        Test nominal relative move operation.
        """
        self.log_divider("Execute Relative Move")
        
        # Get initial position
        initial_pos = self.motion_port.get_current_position()
        self.log_interaction("Test", "GET", "MotionPort", "Initial position",
                           {"position": (initial_pos.x, initial_pos.y)})
        
        # Move relative
        dx, dy = 5.0, 3.0
        self.log_interaction("Test", "CALL", "MotionService", f"move_relative({dx}, {dy})")
        result = self.motion_service.move_relative(dx, dy)
        
        self.log_interaction("Test", "ASSERT", "MotionService", "Move succeeded",
                           {"result": result.is_success}, expect=True, got=result.is_success)
        self.assertTrue(result.is_success, f"Move should succeed")
        
        # Wait for motion to complete
        time.sleep(0.1)
        
        # Verify final position
        final_pos = self.motion_port.get_current_position()
        self.log_interaction("Test", "ASSERT", "MotionPort", "Final position correct",
                           {"expected": (initial_pos.x + dx, initial_pos.y + dy),
                            "got": (final_pos.x, final_pos.y)},
                           expect=(initial_pos.x + dx, initial_pos.y + dy),
                           got=(final_pos.x, final_pos.y))
        
        self.assertAlmostEqual(final_pos.x, initial_pos.x + dx, places=2)
        self.assertAlmostEqual(final_pos.y, initial_pos.y + dy, places=2)
    
    def test_relative_move_negative(self):
        """
        Test relative move with negative values.
        """
        self.log_divider("Execute Negative Relative Move")
        
        # Move to a known position first
        self.motion_service.move_absolute(10.0, 10.0)
        time.sleep(0.1)
        
        initial_pos = self.motion_port.get_current_position()
        
        # Move relative with negative values
        dx, dy = -3.0, -2.0
        self.log_interaction("Test", "CALL", "MotionService", f"move_relative({dx}, {dy})")
        result = self.motion_service.move_relative(dx, dy)
        
        self.assertTrue(result.is_success)
        
        time.sleep(0.1)
        final_pos = self.motion_port.get_current_position()
        
        self.log_interaction("Test", "ASSERT", "MotionPort", "Final position correct",
                           {"expected": (initial_pos.x + dx, initial_pos.y + dy),
                            "got": (final_pos.x, final_pos.y)})
        self.assertAlmostEqual(final_pos.x, initial_pos.x + dx, places=2)
        self.assertAlmostEqual(final_pos.y, initial_pos.y + dy, places=2)


if __name__ == '__main__':
    unittest.main()

