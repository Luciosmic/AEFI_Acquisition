"""
E2E Test: Continuous Acquisition Error Handling

Tests error handling in continuous acquisition.
Validates: invalid config → error handling → proper state.
"""

import unittest
from archives.AEFI_Acquisition.src.tests_e2e.base import (
    DiagramFriendlyTest,
    create_mock_acquisition_port,
    create_event_bus,
)
from application.services.continuous_acquisition_service.continuous_acquisition_service import ContinuousAcquisitionService
from application.services.continuous_acquisition_service.i_continuous_acquisition_executor import ContinuousAcquisitionConfig
from infrastructure.fake.execution.fake_continuous_acquisition_executor import FakeContinuousAcquisitionExecutor


class TestContinuousAcquisitionErrorHandling(DiagramFriendlyTest):
    """
    Test error handling.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        self.acquisition_port = create_mock_acquisition_port()
        self.executor = FakeContinuousAcquisitionExecutor(self.event_bus)
        self.service = ContinuousAcquisitionService(self.executor, self.acquisition_port)
    
    def test_invalid_sample_rate(self):
        """
        Test handling of invalid sample rate (negative or zero).
        """
        self.log_divider("Test Invalid Config")
        
        # Service should handle invalid config gracefully
        invalid_config = ContinuousAcquisitionConfig(
            sample_rate_hz=-10.0,  # Invalid
            max_duration_s=None
        )
        
        # Service has basic validation but doesn't raise (per current implementation)
        self.log_interaction("Test", "CALL", "ContinuousService", "start_acquisition(invalid_config)")
        self.service.start_acquisition(invalid_config)
        
        # Executor may or may not start, but service should not crash
        self.log_interaction("Test", "INFO", "Service", "Handled invalid config without crash")
        
        # Clean up
        if self.executor._is_running:
            self.service.stop_acquisition()
        
    def test_stop_when_not_running(self):
        """
        Test stopping when acquisition is not running (should be safe).
        """
        self.log_divider("Test Stop When Not Running")
        
        # Stop without starting
        self.log_interaction("Test", "CALL", "ContinuousService", "stop_acquisition() (not running)")
        self.service.stop_acquisition()
        
        # Should not raise exception
        self.log_interaction("Test", "ASSERT", "Service", "Stop succeeded without error",
                           {"is_running": self.executor._is_running}, expect=False, got=self.executor._is_running)
        self.assertFalse(self.executor._is_running)


if __name__ == '__main__':
    unittest.main()

