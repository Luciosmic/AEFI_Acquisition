"""
E2E Test: Scan Failure Handling

Tests scan failure scenarios (motion failure, acquisition failure).
Validates: error detection → failure state → proper cleanup.
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
from application.dtos.scan_dtos import Scan2DConfigDTO
from infrastructure.real.execution.step_scan_executor import StepScanExecutor
from domain.models.scan.value_objects import ScanStatus
from domain.models.scan.events.scan_events import ScanFailed


class TestScanFailureHandling(DiagramFriendlyTest):
    """
    Test scan failure handling.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        self.acquisition_port = create_mock_acquisition_port()
        self.scan_executor = StepScanExecutor(None, self.acquisition_port, self.event_bus)
        self.scan_service = ScanApplicationService(
            None,
            self.acquisition_port,
            self.event_bus,
            self.scan_executor
        )
        
        self.config = create_scan_config(
            x_points=3,
            y_points=3,
            stabilization_delay_ms=0,
            averaging=1
        )
        
        # Track failure event
        self.failed_event = None
        def failure_handler(event):
            self.log_interaction("EventBus", "PUBLISH", "TestHandler", "Received ScanFailed")
            self.failed_event = event
        
        self.event_bus.subscribe("scanfailed", failure_handler)
    
    def test_motion_failure_handling(self):
        """
        Test handling of motion failure during scan.
        """
        self.log_divider("Setup Motion Failure")
        
        # Create motion port with failure on next move
        self.motion_port = create_mock_motion_port(
            event_bus=self.event_bus,
            delay_ms=10.0,
            failure_next=True,
            failure_reason="Simulated motion error"
        )
        
        self.scan_executor._motion_port = self.motion_port
        self.scan_service._motion_port = self.motion_port
        
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
        
        self.log_divider("Execute Scan (with failure)")
        self.log_interaction("Test", "CALL", "ScanService", "execute_scan(dto)")
        success = self.scan_service.execute_scan(scan_dto)
        
        # Wait for failure
        timeout = 2.0
        start_time = time.time()
        while self.scan_service.get_status().status != ScanStatus.FAILED.value:
            if time.time() - start_time > timeout:
                break
            time.sleep(0.1)
        
        # Verification
        self.log_divider("Verification")
        
        status = self.scan_service.get_status()
        self.log_interaction("Test", "ASSERT", "ScanService", "Status is FAILED",
                           {"status": status.status}, expect="failed", got=status.status)
        self.assertEqual(status.status, ScanStatus.FAILED.value)
        
        scan = self.scan_service._current_scan
        if scan:
            self.log_interaction("Test", "ASSERT", "StepScan", "Scan status is FAILED",
                               {"status": str(scan.status)}, expect="FAILED", got=str(scan.status))
            self.assertEqual(scan.status, ScanStatus.FAILED)
        
        # Check failure event
        self.log_interaction("Test", "ASSERT", "EventBus", "ScanFailed event emitted",
                           {"event": self.failed_event is not None},
                           expect=True, got=self.failed_event is not None)
        self.assertIsNotNone(self.failed_event, "ScanFailed event should be emitted")


if __name__ == '__main__':
    unittest.main()

