"""
E2E Test: Scan Trajectory Patterns

Tests different scan patterns (serpentine, raster, comb).
Validates: pattern generation → correct point order.
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
from domain.models.scan.scan_trajectory_factory import ScanTrajectoryFactory
from domain.models.scan.value_objects import ScanPattern
from domain.models.scan.value_objects import ScanStatus


class TestScanTrajectoryPatterns(DiagramFriendlyTest):
    """
    Test different scan trajectory patterns.
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
    
    def test_serpentine_pattern(self):
        """Test SERPENTINE pattern generation and execution."""
        self.log_divider("Test SERPENTINE Pattern")
        
        config = create_scan_config(
            x_points=3,
            y_points=3,
            pattern=ScanPattern.SERPENTINE,
            stabilization_delay_ms=0,
            averaging=1
        )
        
        # Verify trajectory
        trajectory = ScanTrajectoryFactory.create_trajectory(config)
        positions = list(trajectory.points)
        
        self.log_interaction("Test", "ASSERT", "Trajectory", "Has 9 positions",
                           {"positions": len(positions)}, expect=9, got=len(positions))
        self.assertEqual(len(positions), 9)
        
        # Verify serpentine order (alternating X direction)
        # First row: left to right
        self.assertEqual(positions[0].x, config.scan_zone.x_min)
        self.assertEqual(positions[2].x, config.scan_zone.x_max)
        # Second row: right to left
        self.assertEqual(positions[3].x, config.scan_zone.x_max)
        self.assertEqual(positions[5].x, config.scan_zone.x_min)
        
        # Execute scan
        scan_dto = Scan2DConfigDTO(
            x_min=config.scan_zone.x_min,
            x_max=config.scan_zone.x_max,
            y_min=config.scan_zone.y_min,
            y_max=config.scan_zone.y_max,
            x_nb_points=config.x_nb_points,
            y_nb_points=config.y_nb_points,
            scan_pattern=config.scan_pattern.name,
            stabilization_delay_ms=config.stabilization_delay_ms,
            averaging_per_position=config.averaging_per_position,
            uncertainty_volts=config.measurement_uncertainty.max_uncertainty_volts
        )
        
        self.log_interaction("Test", "CALL", "ScanService", "execute_scan(dto)")
        success = self.scan_service.execute_scan(scan_dto)
        self.assertTrue(success)
        
        # Wait for completion
        timeout = 5.0
        start_time = time.time()
        while self.scan_service.get_status().status != ScanStatus.COMPLETED.value:
            if time.time() - start_time > timeout:
                self.fail("Scan did not complete")
            time.sleep(0.1)
        
        # Verify completion
        status = self.scan_service.get_status()
        self.assertEqual(status.status, ScanStatus.COMPLETED.value)
    
    def test_raster_pattern(self):
        """Test RASTER pattern generation."""
        self.log_divider("Test RASTER Pattern")
        
        config = create_scan_config(
            x_points=3,
            y_points=3,
            pattern=ScanPattern.RASTER,
            stabilization_delay_ms=0,
            averaging=1
        )
        
        trajectory = ScanTrajectoryFactory.create_trajectory(config)
        positions = list(trajectory.points)
        
        # Verify raster order (always left to right)
        for row in range(3):
            start_idx = row * 3
            self.assertEqual(positions[start_idx].x, config.scan_zone.x_min, f"Row {row} starts at x_min")
            self.assertEqual(positions[start_idx + 2].x, config.scan_zone.x_max, f"Row {row} ends at x_max")
        
        self.log_interaction("Test", "ASSERT", "Trajectory", "Raster pattern verified",
                           {"positions": len(positions)}, expect=9, got=len(positions))
        self.assertEqual(len(positions), 9)
    
    def test_comb_pattern(self):
        """Test COMB pattern generation."""
        self.log_divider("Test COMB Pattern")
        
        config = create_scan_config(
            x_points=3,
            y_points=3,
            pattern=ScanPattern.COMB,
            stabilization_delay_ms=0,
            averaging=1
        )
        
        trajectory = ScanTrajectoryFactory.create_trajectory(config)
        positions = list(trajectory.points)
        
        # Verify comb order (scan each column completely)
        # First column: all Y positions
        self.assertEqual(positions[0].x, config.scan_zone.x_min)
        self.assertEqual(positions[1].x, config.scan_zone.x_min)
        self.assertEqual(positions[2].x, config.scan_zone.x_min)
        # Second column
        self.assertEqual(positions[3].x, config.scan_zone.x_min + (config.scan_zone.x_max - config.scan_zone.x_min) / 2)
        
        self.log_interaction("Test", "ASSERT", "Trajectory", "Comb pattern verified",
                           {"positions": len(positions)}, expect=9, got=len(positions))
        self.assertEqual(len(positions), 9)


if __name__ == '__main__':
    unittest.main()

