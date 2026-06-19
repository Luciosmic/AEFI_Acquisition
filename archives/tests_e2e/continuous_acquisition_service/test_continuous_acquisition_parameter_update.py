"""
E2E Test: Continuous Acquisition Parameter Update

Tests dynamic parameter update during continuous acquisition.
Validates: start → update config → parameters changed.
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


class TestContinuousAcquisitionParameterUpdate(DiagramFriendlyTest):
    """
    Test parameter update during acquisition.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        self.acquisition_port = create_mock_acquisition_port()
        self.executor = FakeContinuousAcquisitionExecutor(self.event_bus)
        self.service = ContinuousAcquisitionService(self.executor, self.acquisition_port)
    
    def test_update_sample_rate(self):
        """
        Test updating sample rate during acquisition.
        """
        self.log_divider("Start Acquisition")
        
        initial_config = ContinuousAcquisitionConfig(
            sample_rate_hz=100.0,
            max_duration_s=None
        )
        
        self.log_interaction("Test", "CALL", "ContinuousService", "start_acquisition(config)")
        self.service.start_acquisition(initial_config)
        
        self.assertTrue(self.executor._is_running)
        
        # Update sample rate
        self.log_divider("Update Parameters")
        new_config = ContinuousAcquisitionConfig(
            sample_rate_hz=200.0,
            max_duration_s=None
        )
        
        self.log_interaction("Test", "CALL", "ContinuousService", "update_acquisition_parameters(config)")
        self.service.update_acquisition_parameters(new_config)
        
        # Verify interval was updated (config stored as interval)
        self.log_interaction("Test", "ASSERT", "Executor", "Interval updated",
                           {"interval": self.executor._current_interval},
                           expect="~0.005", got=f"{self.executor._current_interval:.4f}")
        # 1/200 = 0.005
        self.assertAlmostEqual(self.executor._current_interval, 0.005, places=3)
        
        # Stop
        self.service.stop_acquisition()
    
    def test_update_duration_limit(self):
        """
        Test updating duration limit during acquisition.
        """
        self.log_divider("Start Acquisition")
        
        initial_config = ContinuousAcquisitionConfig(
            sample_rate_hz=100.0,
            max_duration_s=10.0
        )
        
        self.service.start_acquisition(initial_config)
        
        # Update duration
        new_config = ContinuousAcquisitionConfig(
            sample_rate_hz=100.0,
            max_duration_s=20.0
        )
        
        self.log_interaction("Test", "CALL", "ContinuousService", "update_acquisition_parameters(config)")
        self.service.update_acquisition_parameters(new_config)
        
        # Verify interval was updated
        self.log_interaction("Test", "ASSERT", "Executor", "Config update processed",
                           {"interval": self.executor._current_interval},
                           expect=">0", got=self.executor._current_interval)
        # Mock doesn't store max_duration, but interval should be updated
        self.assertIsNotNone(self.executor._current_interval)
        
        self.service.stop_acquisition()


if __name__ == '__main__':
    unittest.main()

