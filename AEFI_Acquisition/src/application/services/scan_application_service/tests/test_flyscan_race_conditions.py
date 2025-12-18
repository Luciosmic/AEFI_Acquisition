"""
Race Condition Tests for FlyScan

Tests to detect race conditions and threading issues in FlyScan execution.
These tests complement the E2E tests by focusing on concurrency issues.
"""

import unittest
import time
from datetime import datetime

from src.application.services.scan_application_service.scan_application_service import ScanApplicationService
from domain.models.scan.value_objects.fly_scan_config import FlyScanConfig
from domain.models.scan.value_objects.scan_zone import ScanZone
from domain.models.scan.value_objects.scan_pattern import ScanPattern
from domain.models.test_bench.value_objects.motion_profile import MotionProfile
from domain.models.scan.value_objects.scan_status import ScanStatus
from domain.models.scan.value_objects.acquisition_rate_capability import AcquisitionRateCapability
from infrastructure.mocks.adapter_mock_fly_scan_executor import MockFlyScanExecutor
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from infrastructure.events.in_memory_event_bus import InMemoryEventBus


class TestFlyScanRaceConditions(unittest.TestCase):
    """Test race conditions and threading issues in FlyScan execution."""

    def setUp(self):
        """Set up test fixtures."""
        # Infrastructure
        self.event_bus = InMemoryEventBus()
        self.motion_port = MockMotionPort()
        self.acquisition_port = MockAcquisitionPort()
        self.fly_scan_executor = MockFlyScanExecutor()

        # Application services
        self.scan_service = ScanApplicationService(
            motion_port=self.motion_port,
            acquisition_port=self.acquisition_port,
            event_bus=self.event_bus,
            scan_executor=None,
            fly_scan_executor=self.fly_scan_executor
        )

    def test_no_thread_exceptions_on_completion(self):
        """
        Test that no exceptions occur in daemon thread when scan completes.
        
        This test specifically targets the race condition where:
        - Scan auto-completes when expected_points is reached
        - Worker thread continues trying to add points
        - Should handle gracefully without exceptions
        """
        # Create config that will generate MORE points than expected_points
        # Small grid (3x3 = 9 expected) but high acquisition rate = many real points
        capability = AcquisitionRateCapability(
            measured_rate_hz=100.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=1.0,
            sample_count=100
        )

        config = FlyScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0),
            x_nb_points=3,  # Small grid = 9 expected points
            y_nb_points=3,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=MotionProfile(
                min_speed=1.0,
                target_speed=5.0,  # Fast motion
                acceleration=2.0,
                deceleration=2.0
            ),
            desired_acquisition_rate_hz=100.0,  # High rate = many real points
            max_spatial_gap_mm=0.5
        )

        # Execute FlyScan
        success = self.scan_service.execute_fly_scan(
            config,
            acquisition_rate_hz=capability.measured_rate_hz
        )
        self.assertTrue(success)

        # Wait for completion
        timeout = 60.0
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.scan_service._current_fly_scan is not None:
                if self.scan_service._current_fly_scan.status.is_final():
                    break
            time.sleep(0.1)

        # Wait a bit more to ensure thread has finished processing
        time.sleep(0.5)

        # CRITICAL: Check for thread exceptions
        thread_errors = self.fly_scan_executor.get_thread_errors()
        self.assertEqual(
            len(thread_errors), 0,
            f"Thread should not raise exceptions. Found: {[str(e) for e in thread_errors]}"
        )

        # Verify scan completed successfully
        fly_scan = self.scan_service._current_fly_scan
        self.assertIsNotNone(fly_scan)
        self.assertEqual(fly_scan.status, ScanStatus.COMPLETED)
        self.assertGreater(len(fly_scan.points), 0)

    def test_race_condition_with_many_points(self):
        """
        Test race condition with configuration that generates many more points than expected.
        
        This test creates a scenario where:
        - expected_points = 9 (3x3 grid)
        - real_points ≈ 50-100 (due to high acquisition rate)
        - Tests that auto-completion doesn't cause exceptions
        """
        capability = AcquisitionRateCapability(
            measured_rate_hz=200.0,  # Very high rate
            measured_std_dev_hz=10.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=1.0,
            sample_count=200
        )

        config = FlyScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=20.0, y_min=0.0, y_max=20.0),  # Larger zone
            x_nb_points=3,  # Small grid = 9 expected
            y_nb_points=3,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=MotionProfile(
                min_speed=2.0,
                target_speed=10.0,  # Very fast
                acceleration=5.0,
                deceleration=5.0
            ),
            desired_acquisition_rate_hz=200.0,  # Very high rate
            max_spatial_gap_mm=0.3  # Tight spacing
        )

        # Execute FlyScan
        success = self.scan_service.execute_fly_scan(
            config,
            acquisition_rate_hz=capability.measured_rate_hz
        )
        self.assertTrue(success)

        # Wait for completion
        timeout = 60.0
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.scan_service._current_fly_scan is not None:
                if self.scan_service._current_fly_scan.status.is_final():
                    break
            time.sleep(0.1)

        # Wait for thread to finish
        time.sleep(1.0)

        # Verify no exceptions
        thread_errors = self.fly_scan_executor.get_thread_errors()
        self.assertEqual(
            len(thread_errors), 0,
            f"Race condition detected! Thread exceptions: {[str(e) for e in thread_errors]}"
        )

        # Verify scan completed
        fly_scan = self.scan_service._current_fly_scan
        self.assertIsNotNone(fly_scan)
        self.assertEqual(fly_scan.status, ScanStatus.COMPLETED)
        
        # Verify we got more points than expected (proving race condition scenario)
        expected_points = config.total_grid_points()
        actual_points = len(fly_scan.points)
        self.assertGreater(actual_points, expected_points,
                          f"Should have more real points ({actual_points}) than expected ({expected_points})")

    def test_concurrent_status_changes(self):
        """
        Test that status changes (complete/cancel) are handled correctly.
        
        Tests that attempting to add points after completion doesn't crash.
        """
        capability = AcquisitionRateCapability(
            measured_rate_hz=50.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=1.0,
            sample_count=50
        )

        config = FlyScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=5.0, y_min=0.0, y_max=5.0),
            x_nb_points=2,  # Very small = 4 expected points
            y_nb_points=2,
            scan_pattern=ScanPattern.RASTER,
            motion_profile=MotionProfile(
                min_speed=1.0,
                target_speed=5.0,
                acceleration=2.0,
                deceleration=2.0
            ),
            desired_acquisition_rate_hz=50.0,
            max_spatial_gap_mm=0.5
        )

        # Execute FlyScan
        success = self.scan_service.execute_fly_scan(
            config,
            acquisition_rate_hz=capability.measured_rate_hz
        )
        self.assertTrue(success)

        # Wait for completion
        timeout = 30.0
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.scan_service._current_fly_scan is not None:
                if self.scan_service._current_fly_scan.status.is_final():
                    break
            time.sleep(0.1)

        # Wait for thread
        time.sleep(0.5)

        # Verify no exceptions from concurrent status changes
        thread_errors = self.fly_scan_executor.get_thread_errors()
        self.assertEqual(
            len(thread_errors), 0,
            f"Concurrent status changes caused exceptions: {[str(e) for e in thread_errors]}"
        )


if __name__ == '__main__':
    unittest.main()

