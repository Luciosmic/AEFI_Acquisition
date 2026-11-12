"""
E2E Test: Continuous Acquisition Start/Stop

Tests continuous acquisition start and stop through ContinuousAcquisitionService.
Validates: start → acquisition running → stop → acquisition stopped.
"""

import unittest
import time
from tests_e2e.base import (
    DiagramFriendlyTest,
    create_mock_acquisition_port,
    create_event_bus,
)
from application.services.continuous_acquisition_service.continuous_acquisition_service import ContinuousAcquisitionService
from application.services.continuous_acquisition_service.i_continuous_acquisition_executor import ContinuousAcquisitionConfig
from infrastructure.fake.execution.fake_continuous_acquisition_executor import FakeContinuousAcquisitionExecutor


class TestContinuousAcquisitionStartStop(DiagramFriendlyTest):
    """
    Test continuous acquisition start and stop.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        self.acquisition_port = create_mock_acquisition_port()
        self.executor = FakeContinuousAcquisitionExecutor(self.event_bus)
        self.service = ContinuousAcquisitionService(self.executor, self.acquisition_port)
    
    def test_start_stop_nominal(self):
        """
        Test nominal start and stop of continuous acquisition.
        """
        self.log_divider("Start Acquisition")
        
        config = ContinuousAcquisitionConfig(
            sample_rate_hz=100.0,
            max_duration_s=5.0
        )
        
        self.log_interaction("Test", "CALL", "ContinuousService", "start_acquisition(config)")
        self.service.start_acquisition(config)
        
        # Verify acquisition is running
        self.log_interaction("Test", "ASSERT", "Executor", "Acquisition is running",
                           {"is_running": self.executor._is_running}, expect=True, got=self.executor._is_running)
        self.assertTrue(self.executor._is_running, "Acquisition should be running")
        
        # Wait a bit
        time.sleep(0.1)
        
        # Stop acquisition
        self.log_divider("Stop Acquisition")
        self.log_interaction("Test", "CALL", "ContinuousService", "stop_acquisition()")
        self.service.stop_acquisition()
        
        # Verify acquisition is stopped
        self.log_interaction("Test", "ASSERT", "Executor", "Acquisition is stopped",
                           {"is_running": self.executor._is_running}, expect=False, got=self.executor._is_running)
        self.assertFalse(self.executor._is_running, "Acquisition should be stopped")
    
    def test_start_without_duration_limit(self):
        """
        Test starting acquisition without duration limit (runs until stop).
        """
        self.log_divider("Start Acquisition (no limit)")
        
        config = ContinuousAcquisitionConfig(
            sample_rate_hz=50.0,
            max_duration_s=None  # No limit
        )
        
        self.log_interaction("Test", "CALL", "ContinuousService", "start_acquisition(config)")
        self.service.start_acquisition(config)
        
        self.assertTrue(self.executor._is_running, "Acquisition should be running")
        
        # Verify it doesn't stop automatically
        time.sleep(0.2)
        self.log_interaction("Test", "ASSERT", "Executor", "Still running after delay",
                           {"is_running": self.executor._is_running}, expect=True, got=self.executor._is_running)
        self.assertTrue(self.executor._is_running, "Acquisition should still be running")
        
        # Stop manually
        self.service.stop_acquisition()
        self.assertFalse(self.executor._is_running, "Acquisition should be stopped")


if __name__ == '__main__':
    unittest.main()

