"""
Integration Test: Scan with AtomicMotion - Diagram-Friendly

This test validates the complete domain logic flow:
1. Create StepScan
2. Generate trajectory (positions)
3. Create AtomicMotions from trajectory
4. Execute motions (simulate with events)
5. Validate scan completion

The test is structured to be easily visualized in sequence diagrams or flowcharts.
"""

import unittest
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add skills to path
skills_path = Path(__file__).parent.parent.parent.parent.parent.parent / "_skills" / "diagram_friendly_test"
sys.path.insert(0, str(skills_path))
from diagram_friendly_test import DiagramFriendlyTest

from domain.models.scan.aggregates.step_scan import StepScan
from domain.models.scan.value_objects.step_scan_config import StepScanConfig
from domain.models.scan.value_objects.scan_zone import ScanZone
from domain.models.scan.value_objects.scan_pattern import ScanPattern
from domain.models.scan.value_objects.scan_status import ScanStatus
from domain.models.scan.value_objects.scan_point_result import ScanPointResult
from domain.models.scan.value_objects.measurement_uncertainty import MeasurementUncertainty
from domain.models.scan.scan_trajectory_factory import ScanTrajectoryFactory
from domain.models.scan.services.motion_profile_selector import MotionProfileSelector
from domain.models.scan.entities.atomic_motion import AtomicMotion
from domain.models.scan.value_objects.motion_state import MotionState
from domain.models.scan.events.motion_events import MotionStarted, MotionCompleted, MotionFailed
from domain.models.scan.events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted
from domain.shared.value_objects.position_2d import Position2D
from domain.models.aefi_device.value_objects.acquisition.voltage_measurement import VoltageMeasurement


class TestScanWithAtomicMotionIntegration(DiagramFriendlyTest):
    """
    Integration test for complete scan flow with AtomicMotion.
    
    Flow Diagram:
    ┌─────────────┐
    │ 1. Setup    │ Create config, selector, scan
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ 2. Generate │ Create trajectory (positions)
    │ Trajectory  │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ 3. Create   │ Generate AtomicMotions from positions
    │ AtomicMotions│
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ 4. Start    │ Start scan, add motions
    │ Scan        │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ 5. Execute  │ For each motion: start → complete → acquire point
    │ Motions     │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ 6. Complete │ Scan completes when all points acquired
    │ Scan        │
    └─────────────┘
    """
    
    def setUp(self):
        """STEP 1: Setup - Create configuration and services."""
        super().setUp()
        self.log_divider("Setup")
        
        # Create scan configuration
        self.log_interaction("Test", "CREATE", "StepScanConfig", "Create scan configuration")
        self.config = StepScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0),
            x_nb_points=3,
            y_nb_points=3,
            scan_pattern=ScanPattern.RASTER,
            stabilization_delay_ms=100,
            averaging_per_position=1,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=1e-6)
        )
        
        # Create motion profile selector
        self.log_interaction("Test", "CREATE", "MotionProfileSelector", "Create profile selector", {"threshold_mm": 5.0})
        self.profile_selector = MotionProfileSelector(small_distance_threshold_mm=5.0)
        
        # Create scan aggregate
        self.log_interaction("Test", "CREATE", "StepScan", "Create scan aggregate")
        self.scan = StepScan()
    
    def test_complete_scan_flow_with_atomic_motions(self):
        """
        Test complete scan flow: trajectory → motions → execution → completion.
        
        Sequence Diagram:
        Scan → TrajectoryFactory → AtomicMotions → StepScan
          │                              │              │
          │─── start() ──────────────────┼──────────────┤
          │                              │              │
          │─── execute_motion(1) ────────┼──────────────┤
          │                              │              │
          │─── motion_started ────────────┼──────────────┤
          │                              │              │
          │─── motion_completed ─────────┼──────────────┤
          │                              │              │
          │─── acquire_point ────────────┼──────────────┤
          │                              │              │
          │─── (repeat for all motions) ─┼──────────────┤
          │                              │              │
          │─── complete() ───────────────┼──────────────┤
        """
        
        # STEP 2: Generate trajectory (positions)
        self.log_divider("Generate Trajectory")
        self.log_interaction("Test", "CALL", "ScanTrajectoryFactory", "create_trajectory(config)")
        trajectory = ScanTrajectoryFactory.create_trajectory(self.config)
        positions = list(trajectory.points)
        
        self.log_interaction("Test", "ASSERT", "Trajectory", f"Has {len(positions)} positions", 
                           {"positions": len(positions)}, expect=9, got=len(positions))
        self.assertGreater(len(positions), 0, "Trajectory should have positions")
        self.assertEqual(len(positions), 9, "3x3 grid should have 9 positions")
        
        # STEP 3: Create AtomicMotions from trajectory
        self.log_divider("Create AtomicMotions")
        self.log_interaction("Test", "CALL", "ScanTrajectoryFactory", "create_motions(positions, selector)")
        motions = ScanTrajectoryFactory.create_motions(positions, self.profile_selector)
        
        self.assertEqual(len(motions), len(positions) - 1, 
                        "Should have N-1 motions for N positions")
        self.assertGreater(len(motions), 0, "Should have at least one motion")
        
        # Verify all motions are in PENDING state
        for motion in motions:
            self.assertEqual(motion.execution_state, MotionState.PENDING)
            self.assertIsNone(motion.execution_motion_id)
        
        # STEP 4: Start scan and add motions
        self.log_divider("Start Scan")
        self.log_interaction("Test", "CALL", "StepScan", "start(config)")
        self.scan.start(self.config)
        self.log_interaction("Test", "ASSERT", "StepScan", "Status is RUNNING", 
                           {"status": str(self.scan.status)}, expect="RUNNING", got=str(self.scan.status))
        self.assertEqual(self.scan.status, ScanStatus.RUNNING)
        
        self.log_interaction("Test", "CALL", "StepScan", "add_motions(motions)")
        self.scan.add_motions(motions)
        self.log_interaction("Test", "ASSERT", "StepScan", f"Has {len(motions)} motions", 
                           {"motions_count": len(self.scan.motions)}, expect=len(motions), got=len(self.scan.motions))
        self.assertEqual(len(self.scan.motions), len(motions))
        
        # Check ScanStarted event
        events = self.scan.domain_events
        self.assertTrue(any(isinstance(e, ScanStarted) for e in events))
        
        # STEP 5: Execute motions (simulate execution flow)
        self.log_divider("Execute Motions")
        current_position = Position2D(x=0.0, y=0.0)  # Starting position
        
        # Add first point (starting position)
        first_measurement = VoltageMeasurement(
            voltage_x_in_phase=1.0,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=datetime.now()
        )
        first_point = ScanPointResult(
            point_index=0,
            position=current_position,
            measurement=first_measurement
        )
        self.log_interaction("Test", "CALL", "StepScan", "add_point_result(point_0)")
        self.scan.add_point_result(first_point)
        
        for i, motion in enumerate(motions):
            # 5a. Start motion
            motion_id = f"motion_{i}_{uuid4().hex[:8]}"
            self.log_interaction("Test", "CALL", f"AtomicMotion_{i}", f"start({motion_id})")
            motion.start(motion_id)
            
            self.log_interaction("Test", "ASSERT", f"AtomicMotion_{i}", "State is EXECUTING",
                               {"state": str(motion.execution_state)}, expect="EXECUTING", got=str(motion.execution_state))
            self.assertEqual(motion.execution_state, MotionState.EXECUTING)
            self.assertEqual(motion.execution_motion_id, motion_id)
            
            # 5b. Simulate motion completion (via event)
            # In real execution, this would come from MotionCompleted event
            self.log_interaction("Test", "CALL", f"AtomicMotion_{i}", "complete()")
            motion.complete()
            
            self.log_interaction("Test", "ASSERT", f"AtomicMotion_{i}", "State is COMPLETED",
                               {"state": str(motion.execution_state)}, expect="COMPLETED", got=str(motion.execution_state))
            self.assertEqual(motion.execution_state, MotionState.COMPLETED)
            
            # 5c. Calculate target position after motion
            target_position = Position2D(
                x=current_position.x + motion.dx,
                y=current_position.y + motion.dy
            )
            
            # 5d. Acquire measurement at target position
            measurement = VoltageMeasurement(
                voltage_x_in_phase=1.0 + (i+1) * 0.1,
                voltage_x_quadrature=0.0,
                voltage_y_in_phase=0.0,
                voltage_y_quadrature=0.0,
                voltage_z_in_phase=0.0,
                voltage_z_quadrature=0.0,
                timestamp=datetime.now()
            )
            
            point_result = ScanPointResult(
                point_index=i+1,
                position=target_position,
                measurement=measurement
            )
            
            self.log_interaction("Test", "CALL", "StepScan", f"add_point_result(point_{i+1})")
            self.scan.add_point_result(point_result)
            
            # Update current position for next motion
            current_position = target_position
        
        # STEP 6: Verify scan completion
        self.log_divider("Verify Completion")
        self.log_interaction("Test", "ASSERT", "StepScan", "Status is COMPLETED",
                           {"status": str(self.scan.status)}, expect="COMPLETED", got=str(self.scan.status))
        self.assertEqual(self.scan.status, ScanStatus.COMPLETED)
        self.log_interaction("Test", "ASSERT", "StepScan", f"Has {len(positions)} points",
                           {"points_count": len(self.scan.points)}, expect=len(positions), got=len(self.scan.points))
        self.assertEqual(len(self.scan.points), len(positions))
        
        # Verify all motions are completed
        for motion in self.scan.motions:
            self.assertEqual(motion.execution_state, MotionState.COMPLETED)
        
        # Check ScanCompleted event
        events = self.scan.domain_events
        self.assertTrue(any(isinstance(e, ScanCompleted) for e in events))
        
        # Verify ScanPointAcquired events (9 points = 9 events)
        point_events = [e for e in events if isinstance(e, ScanPointAcquired)]
        self.assertEqual(len(point_events), len(positions))  # 9 positions = 9 points
    
    def test_motion_failure_handling(self):
        """
        Test handling of motion failure during execution.
        
        Flow:
        Start → Execute Motion 1 (OK) → Execute Motion 2 (FAIL) → Scan Failed
        """
        # Setup
        trajectory = ScanTrajectoryFactory.create_trajectory(self.config)
        positions = list(trajectory.points)
        motions = ScanTrajectoryFactory.create_motions(positions, self.profile_selector)
        
        self.scan.start(self.config)
        self.scan.add_motions(motions)
        
        # Execute first motion successfully
        motion_0 = motions[0]
        motion_0.start("motion_0")
        motion_0.complete()
        
        # Fail second motion
        motion_1 = motions[1]
        motion_1.start("motion_1")
        motion_1.fail("Hardware error: motor stalled")
        
        self.assertEqual(motion_1.execution_state, MotionState.FAILED)
        
        # Scan should fail
        self.scan.fail("Motion execution failed: Hardware error: motor stalled")
        self.assertEqual(self.scan.status, ScanStatus.FAILED)
    
    def test_motion_profile_selection_by_distance(self):
        """
        Test that motion profiles are correctly selected based on distance.
        
        Small distance (< 5mm) → slow profile
        Large distance (>= 5mm) → fast profile
        """
        # Create positions with varying distances
        positions = [
            Position2D(x=0.0, y=0.0),
            Position2D(x=2.0, y=0.0),   # 2mm - small
            Position2D(x=7.0, y=0.0),   # 5mm - large (from previous)
            Position2D(x=7.0, y=1.0),   # 1mm - small
            Position2D(x=7.0, y=10.0), # 9mm - large
        ]
        
        motions = ScanTrajectoryFactory.create_motions(positions, self.profile_selector)
        
        self.assertEqual(len(motions), 4)
        
        # Motion 0: 2mm → slow profile
        self.assertEqual(motions[0].motion_profile, self.profile_selector.slow_profile)
        
        # Motion 1: 5mm → fast profile (at threshold)
        self.assertEqual(motions[1].motion_profile, self.profile_selector.fast_profile)
        
        # Motion 2: 1mm → slow profile
        self.assertEqual(motions[2].motion_profile, self.profile_selector.slow_profile)
        
        # Motion 3: 9mm → fast profile
        self.assertEqual(motions[3].motion_profile, self.profile_selector.fast_profile)
    
    def test_motion_execution_state_transitions(self):
        """
        Test correct state transitions for motion execution.
        
        State Machine:
        PENDING → EXECUTING → COMPLETED
        PENDING → EXECUTING → FAILED
        PENDING → FAILED
        """
        trajectory = ScanTrajectoryFactory.create_trajectory(self.config)
        positions = list(trajectory.points)
        motions = ScanTrajectoryFactory.create_motions(positions, self.profile_selector)
        
        motion = motions[0]
        
        # Initial state
        self.assertEqual(motion.execution_state, MotionState.PENDING)
        
        # PENDING → EXECUTING
        motion.start("motion_1")
        self.assertEqual(motion.execution_state, MotionState.EXECUTING)
        
        # EXECUTING → COMPLETED
        motion.complete()
        self.assertEqual(motion.execution_state, MotionState.COMPLETED)
        
        # Test PENDING → FAILED
        motion2 = motions[1]
        self.assertEqual(motion2.execution_state, MotionState.PENDING)
        motion2.fail("Test failure")
        self.assertEqual(motion2.execution_state, MotionState.FAILED)
    
    def test_scan_with_mixed_motion_profiles(self):
        """
        Test scan execution with mixed motion profiles (slow and fast).
        
        Validates that different motion profiles can coexist in the same scan.
        """
        # Create positions that will generate both slow and fast motions
        positions = [
            Position2D(x=0.0, y=0.0),
            Position2D(x=1.0, y=0.0),   # 1mm → slow
            Position2D(x=6.0, y=0.0),   # 5mm → fast
            Position2D(x=6.0, y=2.0),   # 2mm → slow
            Position2D(x=6.0, y=12.0), # 10mm → fast
        ]
        
        motions = ScanTrajectoryFactory.create_motions(positions, self.profile_selector)
        
        self.scan.start(self.config)
        self.scan.add_motions(motions)
        
        # Verify mixed profiles
        slow_count = sum(1 for m in motions if m.motion_profile == self.profile_selector.slow_profile)
        fast_count = sum(1 for m in motions if m.motion_profile == self.profile_selector.fast_profile)
        
        self.assertGreater(slow_count, 0, "Should have slow motions")
        self.assertGreater(fast_count, 0, "Should have fast motions")
        
        # Execute all motions
        for i, motion in enumerate(motions):
            motion.start(f"motion_{i}")
            motion.complete()
            
            # Create and add point result
            point_result = ScanPointResult(
                point_index=i,
                position=Position2D(x=0.0, y=0.0),  # Simplified
                measurement=VoltageMeasurement(
                    voltage_x_in_phase=1.0,
                    voltage_x_quadrature=0.0,
                    voltage_y_in_phase=0.0,
                    voltage_y_quadrature=0.0,
                    voltage_z_in_phase=0.0,
                    voltage_z_quadrature=0.0,
                    timestamp=datetime.now()
                )
            )
            self.scan.add_point_result(point_result)
        
        # Verify completion
        self.assertEqual(self.scan.status, ScanStatus.COMPLETED)
        self.assertEqual(len(self.scan.points), len(motions))


if __name__ == '__main__':
    unittest.main()

