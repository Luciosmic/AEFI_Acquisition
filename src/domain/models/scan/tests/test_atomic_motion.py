"""
Unit tests for AtomicMotion entity.
"""

import unittest
import math
from domain.models.scan.entities.atomic_motion import AtomicMotion
from domain.models.scan.value_objects.motion_state import MotionState
from domain.models.test_bench.value_objects.motion_profile import MotionProfile


class TestAtomicMotion(unittest.TestCase):
    """Test suite for AtomicMotion entity."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.slow_profile = MotionProfile(
            min_speed=0.1,
            target_speed=1.0,
            acceleration=0.5,
            deceleration=0.5,
        )
        self.fast_profile = MotionProfile(
            min_speed=0.5,
            target_speed=10.0,
            acceleration=5.0,
            deceleration=5.0,
        )
    
    def test_create_motion(self):
        """Test creating an atomic motion."""
        motion = AtomicMotion(
            dx=5.0,
            dy=0.0,
            motion_profile=self.slow_profile
        )
        
        self.assertEqual(motion.dx, 5.0)
        self.assertEqual(motion.dy, 0.0)
        self.assertEqual(motion.motion_profile, self.slow_profile)
        self.assertEqual(motion.execution_state, MotionState.PENDING)
        self.assertIsNone(motion.execution_motion_id)
        self.assertGreater(motion.estimated_duration_seconds, 0)
    
    def test_get_distance(self):
        """Test distance calculation."""
        motion = AtomicMotion(
            dx=3.0,
            dy=4.0,
            motion_profile=self.slow_profile
        )
        
        # 3-4-5 triangle
        self.assertAlmostEqual(motion.get_distance(), 5.0, places=5)
    
    def test_calculate_estimated_duration_full_profile(self):
        """Test duration calculation for full trapezoidal profile."""
        # Large distance that allows full profile
        motion = AtomicMotion(
            dx=100.0,
            dy=0.0,
            motion_profile=self.fast_profile
        )
        
        duration = motion.calculate_estimated_duration()
        self.assertGreater(duration, 0)
        # Should be reasonable (less than distance / min_speed)
        self.assertLess(duration, 100.0 / self.fast_profile.min_speed)
    
    def test_calculate_estimated_duration_short_distance(self):
        """Test duration calculation for short distance (triangular profile)."""
        # Very short distance
        motion = AtomicMotion(
            dx=0.1,
            dy=0.0,
            motion_profile=self.slow_profile
        )
        
        duration = motion.calculate_estimated_duration()
        self.assertGreater(duration, 0)
        # Should be reasonable
        self.assertLess(duration, 10.0)  # Should complete quickly
    
    def test_validation_nan(self):
        """Test validation rejects NaN values."""
        with self.assertRaises(ValueError):
            AtomicMotion(
                dx=float('nan'),
                dy=0.0,
                motion_profile=self.slow_profile
            )
        
        with self.assertRaises(ValueError):
            AtomicMotion(
                dx=0.0,
                dy=float('nan'),
                motion_profile=self.slow_profile
            )
    
    def test_validation_infinite(self):
        """Test validation rejects infinite values."""
        with self.assertRaises(ValueError):
            AtomicMotion(
                dx=float('inf'),
                dy=0.0,
                motion_profile=self.slow_profile
            )
        
        with self.assertRaises(ValueError):
            AtomicMotion(
                dx=0.0,
                dy=float('inf'),
                motion_profile=self.slow_profile
            )
    
    def test_start_motion(self):
        """Test starting a motion."""
        motion = AtomicMotion(
            dx=5.0,
            dy=0.0,
            motion_profile=self.slow_profile
        )
        
        motion.start("motion_123")
        
        self.assertEqual(motion.execution_state, MotionState.EXECUTING)
        self.assertEqual(motion.execution_motion_id, "motion_123")
    
    def test_start_motion_wrong_state(self):
        """Test starting a motion in wrong state raises error."""
        motion = AtomicMotion(
            dx=5.0,
            dy=0.0,
            motion_profile=self.slow_profile
        )
        
        motion.start("motion_123")
        
        # Try to start again
        with self.assertRaises(ValueError):
            motion.start("motion_456")
    
    def test_complete_motion(self):
        """Test completing a motion."""
        motion = AtomicMotion(
            dx=5.0,
            dy=0.0,
            motion_profile=self.slow_profile
        )
        
        motion.start("motion_123")
        motion.complete()
        
        self.assertEqual(motion.execution_state, MotionState.COMPLETED)
    
    def test_complete_motion_wrong_state(self):
        """Test completing a motion in wrong state raises error."""
        motion = AtomicMotion(
            dx=5.0,
            dy=0.0,
            motion_profile=self.slow_profile
        )
        
        # Try to complete without starting
        with self.assertRaises(ValueError):
            motion.complete()
    
    def test_fail_motion_from_pending(self):
        """Test failing a motion from PENDING state."""
        motion = AtomicMotion(
            dx=5.0,
            dy=0.0,
            motion_profile=self.slow_profile
        )
        
        motion.fail("Test error")
        
        self.assertEqual(motion.execution_state, MotionState.FAILED)
    
    def test_fail_motion_from_executing(self):
        """Test failing a motion from EXECUTING state."""
        motion = AtomicMotion(
            dx=5.0,
            dy=0.0,
            motion_profile=self.slow_profile
        )
        
        motion.start("motion_123")
        motion.fail("Test error")
        
        self.assertEqual(motion.execution_state, MotionState.FAILED)
    
    def test_fail_motion_wrong_state(self):
        """Test failing a motion in wrong state raises error."""
        motion = AtomicMotion(
            dx=5.0,
            dy=0.0,
            motion_profile=self.slow_profile
        )
        
        motion.start("motion_123")
        motion.complete()
        
        # Try to fail after completion
        with self.assertRaises(ValueError):
            motion.fail("Test error")


if __name__ == '__main__':
    unittest.main()

