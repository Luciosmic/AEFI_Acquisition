"""
E2E Test: Scan Nominal Flow

Tests the complete nominal flow of a scan execution through ScanApplicationService.
Validates: configuration → trajectory → execution → results.
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
from domain.models.scan.events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted


class TestScanNominalFlow(DiagramFriendlyTest):
    """
    Test the complete nominal flow of scan execution.
    
    Flow:
    1. Setup (service, mocks, config)
    2. Execute scan via service
    3. Verify completion
    4. Verify results
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        # Create infrastructure
        self.log_interaction("Test", "CREATE", "EventBus", "Initialize event bus")
        self.event_bus = create_event_bus()
        
        self.log_interaction("Test", "CREATE", "MotionPort", "Initialize mock motion port")
        self.motion_port = create_mock_motion_port(event_bus=self.event_bus, delay_ms=10.0)
        
        self.log_interaction("Test", "CREATE", "AcquisitionPort", "Initialize mock acquisition port")
        self.acquisition_port = create_mock_acquisition_port()
        
        self.log_interaction("Test", "CREATE", "ScanExecutor", "Initialize scan executor")
        self.scan_executor = StepScanExecutor(self.motion_port, self.acquisition_port, self.event_bus)
        
        self.log_interaction("Test", "CREATE", "ScanService", "Initialize scan application service")
        self.scan_service = ScanApplicationService(
            self.motion_port,
            self.acquisition_port,
            self.event_bus,
            self.scan_executor
        )
        
        # Create scan config
        self.log_interaction("Test", "CREATE", "ScanConfig", "Create scan configuration")
        self.config = create_scan_config(
            x_points=2,
            y_points=2,
            stabilization_delay_ms=0,
            averaging=1
        )
        
        # Track events
        self.events_received = []
        def event_handler(event):
            event_name = type(event).__name__
            self.log_interaction("EventBus", "PUBLISH", "TestHandler", f"Received {event_name}")
            self.events_received.append((event_name, event))
        
        self.event_bus.subscribe("scanstarted", event_handler)
        self.event_bus.subscribe("scanpointacquired", event_handler)
        self.event_bus.subscribe("scancompleted", event_handler)
    
    def test_nominal_scan_execution(self):
        """
        Test complete nominal scan execution flow.
        
        Sequence:
        1. Create DTO from config
        2. Execute scan via service
        3. Wait for completion
        4. Verify scan status and results
        """
        self.log_divider("Execution")
        
        # Convert config to DTO
        self.log_interaction("Test", "CREATE", "ScanDTO", "Create scan DTO from config")
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
        
        # Execute scan
        self.log_interaction("Test", "CALL", "ScanService", "execute_scan(dto)")
        success = self.scan_service.execute_scan(scan_dto)
        
        self.log_interaction("Test", "ASSERT", "ScanService", "Execution started", expect=True, got=success)
        self.assertTrue(success, "Scan execution should start successfully")
        
        # Wait for completion (with timeout)
        # Timeout increased to account for realistic motion durations from domain
        # For a 2x2 scan (3 motions), estimated ~6-7s total
        self.log_divider("Waiting for Completion")
        timeout = 30.0  # Increased to allow realistic motion simulation
        start_time = time.time()
        
        while self.scan_service.get_status().status != ScanStatus.COMPLETED.value:
            if time.time() - start_time > timeout:
                self.fail(f"Scan did not complete within {timeout}s")
            time.sleep(0.1)
        
        elapsed = time.time() - start_time
        self.log_interaction("Test", "INFO", "ScanService", f"Scan completed in {elapsed:.2f}s")
        
        # Verification
        self.log_divider("Verification")
        
        # Check service status
        status = self.scan_service.get_status()
        self.log_interaction("Test", "ASSERT", "ScanService", "Status is COMPLETED",
                           {"status": status.status}, expect="completed", got=status.status)
        self.assertEqual(status.status, ScanStatus.COMPLETED.value)
        
        # Check scan aggregate
        scan = self.scan_service._current_scan
        self.assertIsNotNone(scan, "Current scan should exist")
        
        self.log_interaction("Test", "ASSERT", "StepScan", "Scan status is COMPLETED",
                           {"status": str(scan.status)}, expect="COMPLETED", got=str(scan.status))
        self.assertEqual(scan.status, ScanStatus.COMPLETED)
        
        # Check points acquired
        expected_points = self.config.total_points()
        self.log_interaction("Test", "ASSERT", "StepScan", f"Has {expected_points} points",
                           {"points": len(scan.points)}, expect=expected_points, got=len(scan.points))
        self.assertEqual(len(scan.points), expected_points)
        
        # Check events
        event_names = [name for name, _ in self.events_received]
        
        self.log_interaction("Test", "ASSERT", "EventBus", "ScanStarted event emitted",
                           {"events": event_names}, expect=True, got="ScanStarted" in event_names)
        self.assertTrue(any(name == "ScanStarted" for name in event_names))
        
        self.log_interaction("Test", "ASSERT", "EventBus", f"{expected_points} ScanPointAcquired events",
                           {"count": event_names.count("ScanPointAcquired")},
                           expect=expected_points, got=event_names.count("ScanPointAcquired"))
        self.assertEqual(event_names.count("ScanPointAcquired"), expected_points)
        
        self.log_interaction("Test", "ASSERT", "EventBus", "ScanCompleted event emitted",
                           {"events": event_names}, expect=True, got="ScanCompleted" in event_names)
        self.assertTrue(any(name == "ScanCompleted" for name in event_names))


if __name__ == '__main__':
    unittest.main()

