"""
E2E Test: Motion Control During Scan

Integration test: Manual motion control while scan is running.
Validates: scan start → manual motion → proper handling.
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
from application.services.motion_control_service.motion_control_service import MotionControlService
from application.dtos.scan_dtos import Scan2DConfigDTO
from infrastructure.real.execution.step_scan_executor import StepScanExecutor
from domain.models.scan.value_objects import ScanStatus


class TestMotionDuringScan(DiagramFriendlyTest):
    """
    Test manual motion control during scan execution.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        self.motion_port = create_mock_motion_port(event_bus=self.event_bus, delay_ms=50.0)
        self.acquisition_port = create_mock_acquisition_port()
        self.scan_executor = StepScanExecutor(self.motion_port, self.acquisition_port, self.event_bus)
        self.scan_service = ScanApplicationService(
            self.motion_port,
            self.acquisition_port,
            self.event_bus,
            self.scan_executor
        )
        
        self.motion_service = MotionControlService(self.motion_port, self.event_bus)
        
        self.config = create_scan_config(
            x_points=3,
            y_points=3,
            stabilization_delay_ms=0,
            averaging=1
        )
    
    def test_emergency_stop_during_scan(self):
        """
        Test emergency stop during scan execution.
        """
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
        
        # Wait a bit for scan to start
        time.sleep(0.2)
        
        # Emergency stop via motion service
        self.log_divider("Emergency Stop")
        self.log_interaction("Test", "CALL", "MotionService", "emergency_stop()")
        result = self.motion_service.emergency_stop()
        
        self.log_interaction("Test", "ASSERT", "MotionService", "Emergency stop succeeded",
                           {"result": result.is_success}, expect=True, got=result.is_success)
        self.assertTrue(result.is_success)
        
        # Scan should be cancelled or failed
        time.sleep(0.2)
        status = self.scan_service.get_status()
        self.log_interaction("Test", "ASSERT", "ScanService", "Scan stopped",
                           {"status": status.status}, expect="cancelled or failed", got=status.status)
        
        # Status should be CANCELLED or FAILED
        self.assertIn(status.status, [ScanStatus.CANCELLED.value, ScanStatus.FAILED.value])


if __name__ == '__main__':
    unittest.main()



