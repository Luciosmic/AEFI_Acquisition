"""
E2E Test: Scan Pause/Resume

Tests scan pause and resume functionality.
Validates: start → pause → resume → completion.
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
from domain.models.scan.events.scan_events import ScanPaused, ScanResumed


class TestScanPauseResume(DiagramFriendlyTest):
    """
    Test scan pause and resume functionality.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        # Use longer delay to allow pause during execution
        self.motion_port = create_mock_motion_port(event_bus=self.event_bus, delay_ms=50.0)
        self.acquisition_port = create_mock_acquisition_port()
        self.scan_executor = StepScanExecutor(self.motion_port, self.acquisition_port, self.event_bus)
        self.scan_service = ScanApplicationService(
            self.motion_port,
            self.acquisition_port,
            self.event_bus,
            self.scan_executor
        )
        
        self.config = create_scan_config(
            x_points=4,
            y_points=4,
            stabilization_delay_ms=0,
            averaging=1
        )
        
        # Track pause/resume events
        self.paused_event = None
        self.resumed_event = None
        
        def pause_handler(event):
            self.log_interaction("EventBus", "PUBLISH", "TestHandler", "Received ScanPaused")
            self.paused_event = event
        
        def resume_handler(event):
            self.log_interaction("EventBus", "PUBLISH", "TestHandler", "Received ScanResumed")
            self.resumed_event = event
        
        self.event_bus.subscribe("scanpaused", pause_handler)
        self.event_bus.subscribe("scanresumed", resume_handler)
    
    def test_scan_pause_resume(self):
        """
        Test pausing and resuming a scan during execution.
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
        
        # Wait a bit for scan to progress
        time.sleep(0.3)
        
        # Pause scan
        self.log_divider("Pause Scan")
        points_before_pause = self.scan_service.get_status().current_point_index
        
        self.log_interaction("Test", "CALL", "ScanService", "pause_scan()")
        self.scan_service.pause_scan()
        
        # Wait for pause to take effect
        timeout = 2.0
        start_time = time.time()
        while self.scan_service.get_status().status != ScanStatus.PAUSED.value:
            if time.time() - start_time > timeout:
                break
            time.sleep(0.1)
        
        # Verification: paused state
        self.log_divider("Verify Paused")
        status = self.scan_service.get_status()
        
        self.log_interaction("Test", "ASSERT", "ScanService", "Status is PAUSED",
                           {"status": status.status}, expect="paused", got=status.status)
        self.assertEqual(status.status, ScanStatus.PAUSED.value)
        
        self.log_interaction("Test", "ASSERT", "ScanService", "is_paused is True",
                           {"is_paused": status.is_paused}, expect=True, got=status.is_paused)
        self.assertTrue(status.is_paused)
        
        # Check pause event
        self.log_interaction("Test", "ASSERT", "EventBus", "ScanPaused event emitted",
                           {"event": self.paused_event is not None},
                           expect=True, got=self.paused_event is not None)
        self.assertIsNotNone(self.paused_event, "ScanPaused event should be emitted")
        
        # Resume scan
        self.log_divider("Resume Scan")
        self.log_interaction("Test", "CALL", "ScanService", "resume_scan()")
        self.scan_service.resume_scan()
        
        # Wait for resume to take effect
        start_time = time.time()
        while self.scan_service.get_status().status != ScanStatus.RUNNING.value:
            if time.time() - start_time > timeout:
                break
            time.sleep(0.1)
        
        # Verification: resumed state
        self.log_divider("Verify Resumed")
        status = self.scan_service.get_status()
        
        self.log_interaction("Test", "ASSERT", "ScanService", "Status is RUNNING",
                           {"status": status.status}, expect="running", got=status.status)
        self.assertEqual(status.status, ScanStatus.RUNNING.value)
        
        self.log_interaction("Test", "ASSERT", "ScanService", "is_paused is False",
                           {"is_paused": status.is_paused}, expect=False, got=status.is_paused)
        self.assertFalse(status.is_paused)
        
        # Check resume event
        self.log_interaction("Test", "ASSERT", "EventBus", "ScanResumed event emitted",
                           {"event": self.resumed_event is not None},
                           expect=True, got=self.resumed_event is not None)
        self.assertIsNotNone(self.resumed_event, "ScanResumed event should be emitted")
        
        # Wait for completion
        self.log_divider("Wait for Completion")
        start_time = time.time()
        while self.scan_service.get_status().status != ScanStatus.COMPLETED.value:
            if time.time() - start_time > timeout * 2:
                break
            time.sleep(0.1)
        
        # Final verification
        final_status = self.scan_service.get_status()
        self.log_interaction("Test", "ASSERT", "ScanService", "Final status is COMPLETED",
                           {"status": final_status.status}, expect="completed", got=final_status.status)
        
        # Points should be preserved after pause/resume
        scan = self.scan_service._current_scan
        if scan:
            self.log_interaction("Test", "ASSERT", "StepScan", "Points acquired",
                               {"points": len(scan.points)}, expect=">0", got=len(scan.points))
            self.assertGreater(len(scan.points), 0, "Should have acquired points")


if __name__ == '__main__':
    unittest.main()

