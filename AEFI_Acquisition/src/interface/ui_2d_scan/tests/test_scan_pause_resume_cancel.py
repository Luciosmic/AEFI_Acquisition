"""
Comprehensive Tests for Scan Pause/Resume/Cancel Logic

Tests the interaction between ScanPresenter and ScanApplicationService
for pause, resume, cancel, and restart-after-failure scenarios.
"""

import unittest
from unittest.mock import MagicMock
from typing import Any
import threading
import time

from tool.diagram_friendly_test import DiagramFriendlyTest
from interface.ui_2d_scan.presenter_2d_scan import ScanPresenter
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from infrastructure.mocks.adapter_mock_scan_executor import MockScanExecutor
from infrastructure.events.in_memory_event_bus import InMemoryEventBus

# Import mocks for ports
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort


class TracingSignal:
    """Replaces a pyqtSignal to log emissions."""
    def __init__(self, test_case: DiagramFriendlyTest, name: str):
        self.test_case = test_case
        self.name = name
        self.emissions = []
        
    def emit(self, *args):
        self.test_case.log_interaction(
            actor="ScanPresenter",
            action="EMIT",
            target="UI",
            message=f"Signal {self.name}",
            data={"args": [str(a) for a in args]}
        )
        self.emissions.append(args)


class TestScanPauseResumeCancel(DiagramFriendlyTest):
    """Test suite for scan pause/resume/cancel functionality."""
    
    def setUp(self):
        super().setUp()
        
        # Setup infrastructure
        self.event_bus = InMemoryEventBus()
        self.motion_port = MockMotionPort()
        self.acquisition_port = MockAcquisitionPort()
        
        # Create mock executor with realistic timing
        self.mock_executor = MockScanExecutor(
            event_bus=self.event_bus,
            should_succeed=True,
            point_delay_ms=50  # 50ms per point for testability
        )
        
        # Create service
        self.service = ScanApplicationService(
            motion_port=self.motion_port,
            acquisition_port=self.acquisition_port,
            event_bus=self.event_bus,
            scan_executor=self.mock_executor
        )
        
        # Create presenter
        self.log_interaction("Test", "CREATE", "ScanPresenter", "Initialize Presenter")
        self.presenter = ScanPresenter(
            scan_service=self.service,
            hardware_config_service=MagicMock()  # Not needed for these tests
        )
        
        # Set presenter as output port
        self.service.set_output_port(self.presenter)
        
        # Replace signals with tracing signals
        self.presenter.scan_started = TracingSignal(self, "scan_started")
        self.presenter.scan_point_acquired = TracingSignal(self, "scan_point_acquired")
        self.presenter.scan_completed = TracingSignal(self, "scan_completed")
        self.presenter.scan_failed = TracingSignal(self, "scan_failed")
        self.presenter.scan_progress = TracingSignal(self, "scan_progress")

    def _create_scan_params(self, points=4):
        """Helper to create scan parameters."""
        return {
            'x_min': 0, 'x_max': 1, 'x_nb_points': points,
            'y_min': 0, 'y_max': 1, 'y_nb_points': 1,
            'scan_pattern': 'RASTER',
            'stabilization_delay_ms': 0,
            'averaging_per_position': 1
        }
    
    def test_pause_during_scan(self):
        """Test pausing a scan during execution."""
        self.log_interaction("Test", "START", "ScanPresenter", "Start pause test")
        
        # Start scan in background
        params = self._create_scan_params(points=10)
        self.log_interaction("UI", "CALL", "ScanPresenter", "start_scan", data=params)
        
        # Start scan asynchronously
        scan_thread = threading.Thread(target=self.presenter.start_scan, args=(params,))
        scan_thread.daemon = True
        scan_thread.start()
        
        # Wait for scan to start
        time.sleep(0.1)
        
        # Pause after a few points
        self.log_interaction("UI", "CALL", "ScanPresenter", "pause_scan")
        self.presenter.pause_scan()
        
        # Wait and verify scan is paused
        time.sleep(0.3)
        points_at_pause = len(self.presenter.scan_point_acquired.emissions)
        
        # Wait more and verify no new points acquired
        time.sleep(0.2)
        points_after_wait = len(self.presenter.scan_point_acquired.emissions)
        
        self.log_interaction("Test", "ASSERT", "ScanPresenter", "Check pause stopped acquisition",
                           expect=f"Same count: {points_at_pause}", got=str(points_after_wait))
        self.assertEqual(points_at_pause, points_after_wait, "Scan should not acquire new points when paused")
        
        # Cleanup
        self.presenter.stop_scan()
        scan_thread.join(timeout=2)
    
    def test_resume_after_pause(self):
        """Test resuming a scan after pause."""
        self.log_interaction("Test", "START", "ScanPresenter", "Start resume test")
        
        # Start scan
        params = self._create_scan_params(points=6)
        self.log_interaction("UI", "CALL", "ScanPresenter", "start_scan", data=params)
        
        scan_thread = threading.Thread(target=self.presenter.start_scan, args=(params,))
        scan_thread.daemon = True
        scan_thread.start()
        
        # Wait for scan to start
        time.sleep(0.1)
        
        # Pause
        self.log_interaction("UI", "CALL", "ScanPresenter", "pause_scan")
        self.presenter.pause_scan()
        time.sleep(0.2)
        
        points_at_pause = len(self.presenter.scan_point_acquired.emissions)
        
        # Resume
        self.log_interaction("UI", "CALL", "ScanPresenter", "resume_scan")
        self.presenter.resume_scan()
        
        # Wait for scan to complete
        scan_thread.join(timeout=5)
        
        total_points = len(self.presenter.scan_point_acquired.emissions)
        
        self.log_interaction("Test", "ASSERT", "ScanPresenter", "Check scan completed after resume",
                           expect="6 points", got=f"{total_points} points")
        self.assertEqual(total_points, 6, "Scan should complete all points after resume")
        self.assertGreater(points_at_pause, 0, "Should have acquired some points before pause")
    
    def test_multiple_pause_resume_cycles(self):
        """Test multiple pause/resume cycles during a scan."""
        self.log_interaction("Test", "START", "ScanPresenter", "Start multiple pause/resume test")
        
        params = self._create_scan_params(points=10)
        self.log_interaction("UI", "CALL", "ScanPresenter", "start_scan", data=params)
        
        scan_thread = threading.Thread(target=self.presenter.start_scan, args=(params,))
        scan_thread.daemon = True
        scan_thread.start()
        
        # First pause/resume cycle
        time.sleep(0.15)
        self.log_interaction("UI", "CALL", "ScanPresenter", "pause_scan (cycle 1)")
        self.presenter.pause_scan()
        time.sleep(0.1)
        self.log_interaction("UI", "CALL", "ScanPresenter", "resume_scan (cycle 1)")
        self.presenter.resume_scan()
        
        # Second pause/resume cycle
        time.sleep(0.15)
        self.log_interaction("UI", "CALL", "ScanPresenter", "pause_scan (cycle 2)")
        self.presenter.pause_scan()
        time.sleep(0.1)
        self.log_interaction("UI", "CALL", "ScanPresenter", "resume_scan (cycle 2)")
        self.presenter.resume_scan()
        
        # Wait for completion
        scan_thread.join(timeout=5)
        
        total_points = len(self.presenter.scan_point_acquired.emissions)
        self.log_interaction("Test", "ASSERT", "ScanPresenter", "Check all points acquired",
                           expect="10 points", got=f"{total_points} points")
        self.assertEqual(total_points, 10, "Should complete all points despite multiple pauses")
    
    def test_cancel_during_scan(self):
        """Test cancelling a scan during execution."""
        self.log_interaction("Test", "START", "ScanPresenter", "Start cancel test")
        
        params = self._create_scan_params(points=20)
        self.log_interaction("UI", "CALL", "ScanPresenter", "start_scan", data=params)
        
        scan_thread = threading.Thread(target=self.presenter.start_scan, args=(params,))
        scan_thread.daemon = True
        scan_thread.start()
        
        # Wait for some points
        time.sleep(0.15)
        
        # Cancel
        self.log_interaction("UI", "CALL", "ScanPresenter", "stop_scan")
        self.presenter.stop_scan()
        
        # Wait for thread to finish
        scan_thread.join(timeout=2)
        
        total_points = len(self.presenter.scan_point_acquired.emissions)
        self.log_interaction("Test", "ASSERT", "ScanPresenter", "Check scan stopped early",
                           expect="<20 points", got=f"{total_points} points")
        self.assertLess(total_points, 20, "Scan should stop before completing all points")
        self.assertIn(str(self.service._current_scan.id), self.mock_executor.cancelled_scan_ids,
                     "Executor should record cancellation")
    
    def test_cancel_during_pause(self):
        """Test cancelling a scan while it's paused."""
        self.log_interaction("Test", "START", "ScanPresenter", "Start cancel-during-pause test")
        
        params = self._create_scan_params(points=10)
        self.log_interaction("UI", "CALL", "ScanPresenter", "start_scan", data=params)
        
        scan_thread = threading.Thread(target=self.presenter.start_scan, args=(params,))
        scan_thread.daemon = True
        scan_thread.start()
        
        # Wait and pause
        time.sleep(0.1)
        self.log_interaction("UI", "CALL", "ScanPresenter", "pause_scan")
        self.presenter.pause_scan()
        time.sleep(0.1)
        
        # Cancel while paused
        self.log_interaction("UI", "CALL", "ScanPresenter", "stop_scan (while paused)")
        self.presenter.stop_scan()
        
        # Wait for thread
        scan_thread.join(timeout=2)
        
        total_points = len(self.presenter.scan_point_acquired.emissions)
        self.log_interaction("Test", "ASSERT", "ScanPresenter", "Check scan cancelled",
                           expect="<10 points", got=f"{total_points} points")
        self.assertLess(total_points, 10, "Scan should stop when cancelled during pause")
    
    def test_restart_after_failure(self):
        """Test restarting a scan after a previous scan failed."""
        self.log_interaction("Test", "START", "ScanPresenter", "Start restart-after-failure test")
        
        # Create executor that will fail
        failing_executor = MockScanExecutor(
            event_bus=self.event_bus,
            should_succeed=False,
            point_delay_ms=20,
            fail_at_point=2  # Fail at point 2
        )
        
        # Replace executor with failing one
        self.service._scan_executor = failing_executor
        
        # Start first scan (will fail)
        params1 = self._create_scan_params(points=5)
        self.log_interaction("UI", "CALL", "ScanPresenter", "start_scan (first, will fail)", data=params1)
        
        scan_thread1 = threading.Thread(target=self.presenter.start_scan, args=(params1,))
        scan_thread1.daemon = True
        scan_thread1.start()
        scan_thread1.join(timeout=3)
        
        # Verify first scan failed
        self.log_interaction("Test", "ASSERT", "ScanPresenter", "Check first scan failed")
        self.assertGreater(len(self.presenter.scan_failed.emissions), 0, "First scan should have failed")
        
        # Replace with working executor
        working_executor = MockScanExecutor(
            event_bus=self.event_bus,
            should_succeed=True,
            point_delay_ms=20
        )
        self.service._scan_executor = working_executor
        
        # Reset signals
        self.presenter.scan_point_acquired.emissions = []
        self.presenter.scan_completed.emissions = []
        self.presenter.scan_failed.emissions = []
        
        # Start second scan (should succeed)
        params2 = self._create_scan_params(points=4)
        self.log_interaction("UI", "CALL", "ScanPresenter", "start_scan (second, should succeed)", data=params2)
        
        scan_thread2 = threading.Thread(target=self.presenter.start_scan, args=(params2,))
        scan_thread2.daemon = True
        scan_thread2.start()
        scan_thread2.join(timeout=3)
        
        # Verify second scan succeeded
        total_points = len(self.presenter.scan_point_acquired.emissions)
        completed_count = len(self.presenter.scan_completed.emissions)
        
        self.log_interaction("Test", "ASSERT", "ScanPresenter", "Check second scan succeeded",
                           expect="4 points, 1 completion", got=f"{total_points} points, {completed_count} completion")
        self.assertEqual(total_points, 4, "Second scan should complete all points")
        self.assertEqual(completed_count, 1, "Second scan should emit completion signal")


if __name__ == '__main__':
    unittest.main()
