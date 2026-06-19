"""
E2E Test: Scan Cancellation

Tests scan cancellation during execution.
Validates: start → cancel → proper cleanup.
"""

import unittest
import threading
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
from domain.models.scan.events.scan_events import ScanCancelled


class TestScanCancellation(DiagramFriendlyTest):
    """
    Test scan cancellation during execution.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        # Use longer delay to allow cancellation during execution
        self.motion_port = create_mock_motion_port(event_bus=self.event_bus, delay_ms=100.0)
        self.acquisition_port = create_mock_acquisition_port()
        self.scan_executor = StepScanExecutor(self.motion_port, self.acquisition_port, self.event_bus)
        self.scan_service = ScanApplicationService(
            self.motion_port,
            self.acquisition_port,
            self.event_bus,
            self.scan_executor
        )
        
        self.config = create_scan_config(
            x_points=5,
            y_points=5,
            stabilization_delay_ms=0,
            averaging=1
        )
        
        # Track cancellation event
        self.cancelled_event = None
        def cancel_handler(event):
            self.log_interaction("EventBus", "PUBLISH", "TestHandler", "Received ScanCancelled")
            self.cancelled_event = event
        
        self.event_bus.subscribe("scancancelled", cancel_handler)
    
    def test_scan_cancellation_during_execution(self):
        """
        Test cancelling a scan during execution.
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
        
        # Cancel scan
        self.log_divider("Cancel Scan")
        self.log_interaction("Test", "CALL", "ScanService", "cancel_scan()")
        self.scan_service.cancel_scan()
        
        # Wait for cancellation to complete
        timeout = 2.0
        start_time = time.time()
        while self.scan_service.get_status().status != ScanStatus.CANCELLED.value:
            if time.time() - start_time > timeout:
                break
            time.sleep(0.1)
        
        # Verification
        self.log_divider("Verification")
        
        status = self.scan_service.get_status()
        self.log_interaction("Test", "ASSERT", "ScanService", "Status is CANCELLED",
                           {"status": status.status}, expect="cancelled", got=status.status)
        self.assertEqual(status.status, ScanStatus.CANCELLED.value)
        
        scan = self.scan_service._current_scan
        if scan:
            self.log_interaction("Test", "ASSERT", "StepScan", "Scan status is CANCELLED",
                               {"status": str(scan.status)}, expect="CANCELLED", got=str(scan.status))
            self.assertEqual(scan.status, ScanStatus.CANCELLED)
        
        # Check cancellation event
        self.log_interaction("Test", "ASSERT", "EventBus", "ScanCancelled event emitted",
                           {"event": self.cancelled_event is not None},
                           expect=True, got=self.cancelled_event is not None)
        self.assertIsNotNone(self.cancelled_event, "ScanCancelled event should be emitted")


if __name__ == '__main__':
    unittest.main()

