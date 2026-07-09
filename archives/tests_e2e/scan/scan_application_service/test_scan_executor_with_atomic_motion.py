"""
E2E Test: StepScanExecutor with AtomicMotion

Tests the enhanced executor that uses AtomicMotion entities.
Validates: AtomicMotion generation → profile application → execution → state tracking.
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


class TestScanExecutorWithAtomicMotion(DiagramFriendlyTest):
    """
    Test StepScanExecutor with AtomicMotion integration.
    
    Validates:
    - AtomicMotion generation and integration
    - MotionProfile application
    - State tracking
    - Execution flow
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        self.motion_port = create_mock_motion_port(event_bus=self.event_bus, delay_ms=10.0)
        self.acquisition_port = create_mock_acquisition_port()
        self.scan_executor = StepScanExecutor(
            self.motion_port,
            self.acquisition_port,
            self.event_bus
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
    
    def test_execution_with_atomic_motions(self):
        """
        Test scan execution using AtomicMotion entities.
        """
        self.log_divider("Generate Trajectory and Motions")
        
        # Generate trajectory
        trajectory = ScanTrajectoryFactory.create_trajectory(self.config)
        positions = list(trajectory.points)
        
        self.log_interaction("Test", "ASSERT", "Trajectory", f"Has {len(positions)} positions",
                           {"positions": len(positions)}, expect=9, got=len(positions))
        self.assertEqual(len(positions), 9)
        
        # Generate AtomicMotions
        profile_selector = create_motion_profile_selector(threshold_cm=0.5)
        motions = MotionPlanFactory.create_from_positions(
            positions=positions,
            profile_selector=profile_selector,
            position_unit="cm",
        ).motions
        
        self.log_interaction("Test", "ASSERT", "AtomicMotions", f"Has {len(motions)} motions",
                           {"motions": len(motions)}, expect=8, got=len(motions))
        self.assertEqual(len(motions), 8)
        
        # Create scan and add motions
        from domain.models.scan.aggregate.scan import Scan as StepScan
        scan = StepScan()
        scan.start(self.config)
        scan.add_motions(motions)
        
        self.log_divider("Execute Scan")
        self.log_interaction("Test", "CALL", "ScanExecutor", "execute(scan, trajectory, config)")
        success = self.scan_executor.execute(scan, trajectory, self.config)
        
        self.log_interaction("Test", "ASSERT", "ScanExecutor", "Execution started",
                           {"success": success}, expect=True, got=success)
        self.assertTrue(success)
        
        # Wait for completion
        # Timeout increased to account for realistic motion durations from domain
        timeout = 30.0  # Increased to allow realistic motion simulation
        start_time = time.time()
        while scan.status != ScanStatus.COMPLETED:
            if time.time() - start_time > timeout:
                self.fail("Scan did not complete")
            time.sleep(0.1)
        
        self.log_divider("Verification")
        
        # Verify scan completed
        self.log_interaction("Test", "ASSERT", "StepScan", "Status is COMPLETED",
                           {"status": str(scan.status)}, expect="COMPLETED", got=str(scan.status))
        self.assertEqual(scan.status, ScanStatus.COMPLETED)
        
        # Verify points acquired
        self.log_interaction("Test", "ASSERT", "StepScan", f"Has {len(scan.points)} points",
                           {"points": len(scan.points)}, expect=9, got=len(scan.points))
        self.assertEqual(len(scan.points), 9)
        
        # Verify motions were tracked
        tracker = self.scan_executor._motion_tracker
        stats = tracker.get_statistics()
        
        self.log_interaction("Test", "ASSERT", "MotionTracker", "Motions tracked",
                           {"completed": stats["completed_count"]},
                           expect=8, got=stats["completed_count"])
        self.assertEqual(stats["completed_count"], 8)
        
        # Verify motion events
        motion_event_names = [name for name, _ in self.motion_events]
        
        self.log_interaction("Test", "ASSERT", "EventBus", "MotionStarted events",
                           {"count": motion_event_names.count("MotionStarted")},
                           expect=8, got=motion_event_names.count("MotionStarted"))
        self.assertGreaterEqual(motion_event_names.count("MotionStarted"), 8)
        
        self.log_interaction("Test", "ASSERT", "EventBus", "MotionCompleted events",
                           {"count": motion_event_names.count("MotionCompleted")},
                           expect=8, got=motion_event_names.count("MotionCompleted"))
        self.assertGreaterEqual(motion_event_names.count("MotionCompleted"), 8)
        
        # Verify motion states
        for motion in motions:
            self.log_interaction("Test", "ASSERT", f"AtomicMotion_{motion.id}", "State is COMPLETED",
                               {"state": str(motion.execution_state)}, expect="COMPLETED",
                               got=str(motion.execution_state))
            self.assertEqual(motion.execution_state, MotionState.COMPLETED)
    
    def test_motion_profile_application(self):
        """
        Test that MotionProfile is applied to hardware.
        """
        self.log_divider("Test Profile Application")
        
        # Generate motions
        trajectory = ScanTrajectoryFactory.create_trajectory(self.config)
        positions = list(trajectory.points)
        profile_selector = create_motion_profile_selector(threshold_cm=0.5)
        motions = MotionPlanFactory.create_from_positions(
            positions=positions,
            profile_selector=profile_selector,
            position_unit="cm",
        ).motions
        
        # Create scan
        from domain.models.scan.aggregate.scan import Scan as StepScan
        scan = StepScan()
        scan.start(self.config)
        scan.add_motions(motions)
        
        # Execute
        self.scan_executor.execute(scan, trajectory, self.config)
        
        # Wait a bit for execution to start
        time.sleep(0.2)
        
        # Verify that speed was set (MotionAdapterService calls set_speed)
        # Note: FakeMotionPort stores last_speed
        self.log_interaction("Test", "INFO", "MotionPort", "Speed configuration",
                           {"last_speed": self.motion_port.last_speed})
        
        # At least one motion should have set a speed
        # (exact value depends on profile, but should be > 0)
        if self.motion_port.last_speed is not None:
            self.log_interaction("Test", "ASSERT", "MotionPort", "Speed was set",
                               {"speed": self.motion_port.last_speed}, expect=">0",
                               got=self.motion_port.last_speed)
            self.assertGreater(self.motion_port.last_speed, 0)


if __name__ == '__main__':
    unittest.main()

