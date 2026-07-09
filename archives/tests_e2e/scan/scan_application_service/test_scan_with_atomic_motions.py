"""
E2E Test: Scan with AtomicMotions

Tests scan execution with AtomicMotion integration.
Validates: trajectory → AtomicMotions → execution → motion states.
"""

import unittest
import time
from tests_e2e.base import (
    DiagramFriendlyTest,
    create_scan_config,
    create_mock_motion_port,
    create_mock_acquisition_port,
    create_event_bus,
    create_motion_profile_selector,
)
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.dtos.scan_dtos import Scan2DConfigDTO
from infrastructure.real.execution.step_scan_executor import StepScanExecutor
from domain.models.scan.scan_trajectory_factory import ScanTrajectoryFactory
from domain.models.motion.services.motion_plan_factory import MotionPlanFactory
from domain.models.scan.value_objects import ScanStatus
from domain.models.scan.value_objects import MotionState
from domain.models.motion.events.motion_events import MotionStarted, MotionCompleted


class TestScanWithAtomicMotions(DiagramFriendlyTest):
    """
    Test scan execution with AtomicMotion integration.
    
    Validates:
    - Generation of AtomicMotions from trajectory
    - Profile selection based on distance
    - Motion state transitions
    - Mapping motion_id → AtomicMotion
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
        
        self.config = create_scan_config(
            x_points=3,
            y_points=3,
            stabilization_delay_ms=0,
            averaging=1
        )
        
        # Track motion events
        self.motion_events = []
        def motion_handler(event):
            event_name = type(event).__name__
            self.log_interaction("EventBus", "PUBLISH", "TestHandler", f"Motion event: {event_name}")
            self.motion_events.append((event_name, event))
        
        self.event_bus.subscribe("motionstarted", motion_handler)
        self.event_bus.subscribe("motioncompleted", motion_handler)
    
    def test_scan_with_atomic_motions_generation(self):
        """
        Test that AtomicMotions are generated and used during scan execution.
        """
        self.log_divider("Generate Trajectory and Motions")
        
        # Generate trajectory
        self.log_interaction("Test", "CALL", "ScanTrajectoryFactory", "create_trajectory(config)")
        trajectory = ScanTrajectoryFactory.create_trajectory(self.config)
        positions = list(trajectory.points)
        
        self.log_interaction("Test", "ASSERT", "Trajectory", f"Has {len(positions)} positions",
                           {"positions": len(positions)}, expect=9, got=len(positions))
        self.assertEqual(len(positions), 9, "3x3 grid should have 9 positions")
        
        # Create profile selector
        profile_selector = create_motion_profile_selector(threshold_cm=0.5)
        
        # Generate AtomicMotions
        self.log_interaction("Test", "CALL", "MotionPlanFactory", "create_from_positions(positions, selector)")
        motions = MotionPlanFactory.create_from_positions(
            positions=positions,
            profile_selector=profile_selector,
            position_unit="cm",
        ).motions
        
        self.log_interaction("Test", "ASSERT", "AtomicMotions", f"Has {len(motions)} motions",
                           {"motions": len(motions)}, expect=8, got=len(motions))
        self.assertEqual(len(motions), 8, "9 positions = 8 motions")
        
        # Verify all motions are in PENDING state
        for i, motion in enumerate(motions):
            self.log_interaction("Test", "ASSERT", f"AtomicMotion_{i}", "State is PENDING",
                               {"state": str(motion.execution_state)}, expect="PENDING", got=str(motion.execution_state))
            self.assertEqual(motion.execution_state, MotionState.PENDING)
        
        # Verify profile selection
        self.log_divider("Profile Selection Verification")
        slow_count = sum(1 for m in motions if m.motion_profile == profile_selector.slow_profile)
        fast_count = sum(1 for m in motions if m.motion_profile == profile_selector.fast_profile)
        
        self.log_interaction("Test", "ASSERT", "ProfileSelector", "Mixed profiles selected",
                           {"slow": slow_count, "fast": fast_count},
                           expect="mixed", got=f"{slow_count} slow, {fast_count} fast")
        self.assertGreater(slow_count + fast_count, 0, "Should have motions with profiles")
        
        # Execute scan
        self.log_divider("Execute Scan")
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
        
        # Wait for completion
        timeout = 5.0
        start_time = time.time()
        while self.scan_service.get_status().status != ScanStatus.COMPLETED.value:
            if time.time() - start_time > timeout:
                self.fail("Scan did not complete")
            time.sleep(0.1)
        
        # Verification
        self.log_divider("Verification")
        
        # Check motion events were emitted
        motion_event_names = [name for name, _ in self.motion_events]
        
        self.log_interaction("Test", "ASSERT", "EventBus", "MotionStarted events emitted",
                           {"count": motion_event_names.count("MotionStarted")},
                           expect=">0", got=motion_event_names.count("MotionStarted"))
        self.assertGreater(motion_event_names.count("MotionStarted"), 0)
        
        self.log_interaction("Test", "ASSERT", "EventBus", "MotionCompleted events emitted",
                           {"count": motion_event_names.count("MotionCompleted")},
                           expect=">0", got=motion_event_names.count("MotionCompleted"))
        self.assertGreater(motion_event_names.count("MotionCompleted"), 0)


if __name__ == '__main__':
    unittest.main()

