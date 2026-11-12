"""
E2E Test: Motion Reference Setting

Tests reference position setting through MotionControlService.
Validates: set_reference → position redefined → subsequent moves use new reference.
"""

import unittest
import time
from tests_e2e.base import (
    DiagramFriendlyTest,
    create_mock_motion_port,
    create_event_bus,
)
from application.services.motion_control_service.motion_control_service import MotionControlService


class TestMotionReferenceSetting(DiagramFriendlyTest):
    """
    Test reference position setting.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        self.motion_port = create_mock_motion_port(event_bus=self.event_bus, delay_ms=10.0)
        self.motion_service = MotionControlService(self.motion_port, self.event_bus)
    
    def test_set_reference_x(self):
        """
        Test setting X axis reference.
        """
        self.log_divider("Execute Set Reference X")
        
        # Move to a position
        self.motion_service.move_absolute(10.0, 5.0)
        time.sleep(0.1)
        
        # Set X reference to 0
        self.log_interaction("Test", "CALL", "MotionService", "set_reference('x', 0.0)")
        result = self.motion_service.set_reference("x", 0.0)
        
        self.log_interaction("Test", "ASSERT", "MotionService", "Set reference succeeded",
                           {"result": result.is_success}, expect=True, got=result.is_success)
        self.assertTrue(result.is_success, "Set reference should succeed")
        
        # Verify position is now (0, 5)
        final_pos = self.motion_port.get_current_position()
        self.log_interaction("Test", "ASSERT", "MotionPort", "X reference set to 0",
                           {"x": final_pos.x, "y": final_pos.y},
                           expect=(0.0, 5.0), got=(final_pos.x, final_pos.y))
        
        self.assertAlmostEqual(final_pos.x, 0.0, places=2)
        self.assertAlmostEqual(final_pos.y, 5.0, places=2)
    
    def test_set_reference_y(self):
        """
        Test setting Y axis reference.
        """
        self.log_divider("Execute Set Reference Y")
        
        # Move to a position
        self.motion_service.move_absolute(10.0, 5.0)
        time.sleep(0.1)
        
        # Set Y reference to 0
        self.log_interaction("Test", "CALL", "MotionService", "set_reference('y', 0.0)")
        result = self.motion_service.set_reference("y", 0.0)
        
        self.assertTrue(result.is_success)
        time.sleep(0.1)
        
        # Verify position is now (10, 0)
        final_pos = self.motion_port.get_current_position()
        self.log_interaction("Test", "ASSERT", "MotionPort", "Y reference set to 0",
                           {"x": final_pos.x, "y": final_pos.y},
                           expect=(10.0, 0.0), got=(final_pos.x, final_pos.y))
        
        self.assertAlmostEqual(final_pos.x, 10.0, places=2)
        self.assertAlmostEqual(final_pos.y, 0.0, places=2)


if __name__ == '__main__':
    unittest.main()

