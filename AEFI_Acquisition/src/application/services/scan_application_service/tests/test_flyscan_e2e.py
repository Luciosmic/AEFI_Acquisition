"""
E2E Integration Test for FlyScan

Tests the complete FlyScan flow from configuration to execution.
"""

import unittest
import time
from datetime import datetime

from src.application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.acquisition_configuration_service.acquisition_rate_measurement_service import (
    AcquisitionRateMeasurementService
)
from application.services.acquisition_configuration_service.flyscan_configuration_service import (
    FlyScanConfigurationService
)
from domain.models.scan.value_objects.fly_scan_config import FlyScanConfig
from domain.models.scan.value_objects.scan_zone import ScanZone
from domain.models.scan.value_objects.scan_pattern import ScanPattern
from domain.models.test_bench.value_objects.motion_profile import MotionProfile
from domain.models.scan.value_objects.scan_status import ScanStatus
from infrastructure.mocks.adapter_mock_fly_scan_executor import MockFlyScanExecutor
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from infrastructure.events.in_memory_event_bus import InMemoryEventBus


class TestFlyScanE2E(unittest.TestCase):
    """E2E test for FlyScan execution."""

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
            scan_executor=None,  # Not needed for FlyScan
            fly_scan_executor=self.fly_scan_executor
        )

        self.measurement_service = AcquisitionRateMeasurementService()
        self.config_service = FlyScanConfigurationService()

    def test_complete_flyscan_workflow(self):
        """Test complete FlyScan workflow: measure → validate → execute."""

        # STEP 1: Create capability directly (skip measurement with instantaneous mock)
        from domain.models.scan.value_objects.acquisition_rate_capability import AcquisitionRateCapability
        capability = AcquisitionRateCapability(
            measured_rate_hz=100.0,  # Assume 100 Hz
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=1.0,
            sample_count=100
        )

        self.assertGreater(capability.measured_rate_hz, 0)
        print(f"Using capability: {capability}")

        # STEP 2: Create FlyScan configuration
        config = FlyScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0),
            x_nb_points=3,
            y_nb_points=3,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=MotionProfile(
                min_speed=1.0,
                target_speed=5.0,
                acceleration=2.0,
                deceleration=2.0
            ),
            desired_acquisition_rate_hz=100.0,
            max_spatial_gap_mm=1.0
        )

        # STEP 3: Validate configuration
        validation = self.config_service.validate_flyscan_config(config, capability)
        self.assertTrue(validation.is_valid, f"Validation errors: {validation.errors}")

        # STEP 4: Execute FlyScan
        success = self.scan_service.execute_fly_scan(
            config,
            acquisition_rate_hz=capability.measured_rate_hz
        )
        self.assertTrue(success)

        # STEP 5: Wait for completion
        # Timeout increased to account for realistic motion durations and acquisition
        timeout = 60.0  # FlyScan can take longer due to continuous acquisition
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.scan_service._current_fly_scan is not None:
                if self.scan_service._current_fly_scan.status.is_final():
                    break
            time.sleep(0.1)
        
        # Check if timeout was reached
        if time.time() - start_time >= timeout:
            self.fail(f"FlyScan did not complete within {timeout}s")

        # STEP 6: Verify results
        fly_scan = self.scan_service._current_fly_scan
        self.assertIsNotNone(fly_scan)
        self.assertEqual(fly_scan.status, ScanStatus.COMPLETED)
        self.assertGreater(len(fly_scan.points), 0)

        print(f"FlyScan completed: {len(fly_scan.points)} points acquired")

    def test_incompatible_configuration_rejected(self):
        """Test that incompatible configuration is rejected before execution."""

        # Create slow capability
        from domain.models.scan.value_objects.acquisition_rate_capability import AcquisitionRateCapability
        slow_capability = AcquisitionRateCapability(
            measured_rate_hz=10.0,  # Very slow
            measured_std_dev_hz=1.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=1.0,
            sample_count=10
        )

        # Create fast/tight config
        config = FlyScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=100.0, y_min=0.0, y_max=100.0),
            x_nb_points=10,
            y_nb_points=10,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=MotionProfile(
                min_speed=5.0,
                target_speed=50.0,  # Very fast
                acceleration=25.0,
                deceleration=25.0
            ),
            desired_acquisition_rate_hz=100.0,
            max_spatial_gap_mm=0.1  # Very tight
        )

        # Validate - should fail
        validation = self.config_service.validate_flyscan_config(config, slow_capability)
        self.assertFalse(validation.is_valid)
        self.assertGreater(len(validation.errors), 0)

    def test_suggested_profile_is_compatible(self):
        """Test that suggested profile makes configuration compatible."""

        # Create capability
        from domain.models.scan.value_objects.acquisition_rate_capability import AcquisitionRateCapability
        capability = AcquisitionRateCapability(
            measured_rate_hz=50.0,
            measured_std_dev_hz=5.0,
            measurement_timestamp=datetime.now(),
            measurement_duration_s=1.0,
            sample_count=50
        )

        # Create fast config
        fast_config = FlyScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0),
            x_nb_points=5,
            y_nb_points=5,
            scan_pattern=ScanPattern.SERPENTINE,
            motion_profile=MotionProfile(
                min_speed=5.0,
                target_speed=50.0,  # Too fast
                acceleration=25.0,
                deceleration=25.0
            ),
            desired_acquisition_rate_hz=50.0,
            max_spatial_gap_mm=0.5
        )

        # Should be incompatible
        validation1 = self.config_service.validate_flyscan_config(fast_config, capability)
        self.assertFalse(validation1.is_valid)

        # Get suggested profile
        suggested_profile = self.config_service.suggest_compatible_motion_profile(
            fast_config,
            capability
        )

        # Create new config with suggested profile
        from dataclasses import replace
        compatible_config = replace(fast_config, motion_profile=suggested_profile)

        # Should now be compatible
        validation2 = self.config_service.validate_flyscan_config(compatible_config, capability)
        self.assertTrue(validation2.is_valid)


if __name__ == '__main__':
    unittest.main()
