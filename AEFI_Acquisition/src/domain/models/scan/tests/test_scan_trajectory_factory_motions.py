"""
Unit tests for ScanTrajectoryFactory.create_motions() method.
"""

import unittest
from domain.models.scan.scan_trajectory_factory import ScanTrajectoryFactory
from domain.models.scan.services.motion_profile_selector import MotionProfileSelector
from domain.shared.value_objects.position_2d import Position2D
from domain.models.scan.entities.atomic_motion import AtomicMotion
from domain.models.scan.value_objects.motion_state import MotionState


class TestScanTrajectoryFactoryMotions(unittest.TestCase):
    """Test suite for ScanTrajectoryFactory.create_motions()."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.profile_selector = MotionProfileSelector(small_distance_threshold_mm=5.0)
    
    def test_create_motions_empty_list(self):
        """Test creating motions from empty position list."""
        motions = ScanTrajectoryFactory.create_motions([], self.profile_selector)
        
        self.assertEqual(len(motions), 0)
    
    def test_create_motions_single_position(self):
        """Test creating motions from single position (should return empty)."""
        positions = [Position2D(x=0.0, y=0.0)]
        motions = ScanTrajectoryFactory.create_motions(positions, self.profile_selector)
        
        self.assertEqual(len(motions), 0)
    
    def test_create_motions_two_positions(self):
        """Test creating motions from two positions."""
        positions = [
            Position2D(x=0.0, y=0.0),
            Position2D(x=5.0, y=0.0)
        ]
        motions = ScanTrajectoryFactory.create_motions(positions, self.profile_selector)
        
        self.assertEqual(len(motions), 1)
        motion = motions[0]
        self.assertEqual(motion.dx, 5.0)
        self.assertEqual(motion.dy, 0.0)
        self.assertEqual(motion.execution_state, MotionState.PENDING)
    
    def test_create_motions_multiple_positions(self):
        """Test creating motions from multiple positions."""
        positions = [
            Position2D(x=0.0, y=0.0),
            Position2D(x=5.0, y=0.0),
            Position2D(x=5.0, y=5.0),
            Position2D(x=0.0, y=5.0),
        ]
        motions = ScanTrajectoryFactory.create_motions(positions, self.profile_selector)
        
        self.assertEqual(len(motions), 3)
        
        # First motion: (0,0) -> (5,0)
        self.assertEqual(motions[0].dx, 5.0)
        self.assertEqual(motions[0].dy, 0.0)
        
        # Second motion: (5,0) -> (5,5)
        self.assertEqual(motions[1].dx, 0.0)
        self.assertEqual(motions[1].dy, 5.0)
        
        # Third motion: (5,5) -> (0,5)
        self.assertEqual(motions[2].dx, -5.0)
        self.assertEqual(motions[2].dy, 0.0)
    
    def test_create_motions_profile_selection_small_distance(self):
        """Test profile selection for small distances."""
        positions = [
            Position2D(x=0.0, y=0.0),
            Position2D(x=2.0, y=0.0)  # 2mm distance (below threshold)
        ]
        motions = ScanTrajectoryFactory.create_motions(positions, self.profile_selector)
        
        self.assertEqual(len(motions), 1)
        # Should use slow profile (distance < 5mm)
        self.assertEqual(motions[0].motion_profile, self.profile_selector.slow_profile)
    
    def test_create_motions_profile_selection_large_distance(self):
        """Test profile selection for large distances."""
        positions = [
            Position2D(x=0.0, y=0.0),
            Position2D(x=10.0, y=0.0)  # 10mm distance (above threshold)
        ]
        motions = ScanTrajectoryFactory.create_motions(positions, self.profile_selector)
        
        self.assertEqual(len(motions), 1)
        # Should use fast profile (distance >= 5mm)
        self.assertEqual(motions[0].motion_profile, self.profile_selector.fast_profile)
    
    def test_create_motions_diagonal_movement(self):
        """Test creating motions for diagonal movement."""
        positions = [
            Position2D(x=0.0, y=0.0),
            Position2D(x=3.0, y=4.0)  # 3-4-5 triangle
        ]
        motions = ScanTrajectoryFactory.create_motions(positions, self.profile_selector)
        
        self.assertEqual(len(motions), 1)
        motion = motions[0]
        self.assertEqual(motion.dx, 3.0)
        self.assertEqual(motion.dy, 4.0)
        # Distance should be 5.0 (3-4-5 triangle)
        self.assertAlmostEqual(motion.get_distance(), 5.0, places=5)
        # Should use fast profile (distance >= 5mm)
        self.assertEqual(motion.motion_profile, self.profile_selector.fast_profile)
    
    def test_create_motions_all_have_estimated_duration(self):
        """Test that all created motions have estimated duration calculated."""
        positions = [
            Position2D(x=0.0, y=0.0),
            Position2D(x=5.0, y=0.0),
            Position2D(x=5.0, y=5.0),
        ]
        motions = ScanTrajectoryFactory.create_motions(positions, self.profile_selector)
        
        for motion in motions:
            self.assertGreater(motion.estimated_duration_seconds, 0)
            self.assertIsInstance(motion.estimated_duration_seconds, float)
    
    def test_create_motions_all_in_pending_state(self):
        """Test that all created motions start in PENDING state."""
        positions = [
            Position2D(x=0.0, y=0.0),
            Position2D(x=5.0, y=0.0),
            Position2D(x=5.0, y=5.0),
        ]
        motions = ScanTrajectoryFactory.create_motions(positions, self.profile_selector)
        
        for motion in motions:
            self.assertEqual(motion.execution_state, MotionState.PENDING)
            self.assertIsNone(motion.execution_motion_id)


if __name__ == '__main__':
    unittest.main()

