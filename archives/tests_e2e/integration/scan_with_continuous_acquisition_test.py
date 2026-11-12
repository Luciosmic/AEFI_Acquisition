"""
E2E Test: Scan with Continuous Acquisition

Integration test: Scan execution while continuous acquisition is running.
Validates: continuous acquisition → scan start → both running → completion.
"""

import unittest
import time
from tests_e2e.base import (
    DiagramFriendlyTest,
    create_scan_config,
    create_mock_motion_port,
    create_mock_acquisition_port,
    create_event_bus,
)
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.continuous_acquisition_service.continuous_acquisition_service import ContinuousAcquisitionService
from application.services.continuous_acquisition_service.i_continuous_acquisition_executor import ContinuousAcquisitionConfig
from application.dtos.scan_dtos import Scan2DConfigDTO
from infrastructure.real.execution.step_scan_executor import StepScanExecutor
from infrastructure.fake.execution.fake_continuous_acquisition_executor import FakeContinuousAcquisitionExecutor
from domain.models.scan.value_objects import ScanStatus


class TestScanWithContinuousAcquisition(DiagramFriendlyTest):
    """
    Test scan execution with continuous acquisition running.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        self.motion_port = create_mock_motion_port(event_bus=self.event_bus, delay_ms=10.0)
        self.acquisition_port = create_mock_acquisition_port()
        self.scan_executor = StepScanExecutor(self.motion_port, self.acquisition_port, self.event_bus)
        self.scan_service = ScanApplicationService(
            self.motion_port,
            self.acquisition_port,
            self.event_bus,
            self.scan_executor
        )
        
        self.continuous_executor = FakeContinuousAcquisitionExecutor(self.event_bus)
        self.continuous_service = ContinuousAcquisitionService(self.continuous_executor, self.acquisition_port)
        
        self.config = create_scan_config(
            x_points=2,
            y_points=2,
            stabilization_delay_ms=0,
            averaging=1
        )
    
    def test_scan_during_continuous_acquisition(self):
        """
        Test executing a scan while continuous acquisition is running.
        """
        self.log_divider("Start Continuous Acquisition")
        
        continuous_config = ContinuousAcquisitionConfig(
            sample_rate_hz=100.0,
            max_duration_s=None
        )
        
        self.log_interaction("Test", "CALL", "ContinuousService", "start_acquisition(config)")
        self.continuous_service.start_acquisition(continuous_config)
        
        self.assertTrue(self.continuous_executor._is_running, "Continuous acquisition should be running")
        
        # Start scan
        self.log_divider("Start Scan")
        scan_dto = Scan2DConfigDTO(
            x_min=self.config.scan_zone.x_min,
            x_max=self.config.scan_zone.x_max,
            y_min=self.config.scan_zone.y_min,
            y_max=self.config.scan_zone.y_max,
            x_nb_points=self.config.x_nb_points,
            y_nb_points=self.config.y_nb_points,
            scan_pattern=self.config.scan_pattern.name,
            stabilization_delay_ms=self.config.stabilization_delay_ms,
            averaging_per_position=self.config.averaging_per_position,
            uncertainty_volts=self.config.measurement_uncertainty.max_uncertainty_volts
        )
        
        self.log_interaction("Test", "CALL", "ScanService", "execute_scan(dto)")
        success = self.scan_service.execute_scan(scan_dto)
        self.assertTrue(success)
        
        # Wait for scan completion
        timeout = 5.0
        start_time = time.time()
        while self.scan_service.get_status().status != ScanStatus.COMPLETED.value:
            if time.time() - start_time > timeout:
                break
            time.sleep(0.1)
        
        # Verify scan completed
        status = self.scan_service.get_status()
        self.log_interaction("Test", "ASSERT", "ScanService", "Scan completed",
                           {"status": status.status}, expect="completed", got=status.status)
        self.assertEqual(status.status, ScanStatus.COMPLETED.value)
        
        # Continuous acquisition may still be running or stopped
        self.log_interaction("Test", "INFO", "ContinuousService", "Continuous acquisition state",
                           {"is_running": self.continuous_executor._is_running})
        
        # Clean up
        if self.continuous_executor._is_running:
            self.continuous_service.stop_acquisition()


if __name__ == '__main__':
    unittest.main()

