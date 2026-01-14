"""
Unit Tests for AtomicMotion FlyScan Extensions

Tests the new FlyScan-specific methods added to AtomicMotion:
- get_velocity_at_time()
- calculate_acquisition_positions()
"""

import unittest

from domain.models.scan.entities.atomic_motion import AtomicMotion
from domain.models.test_bench.value_objects.motion_profile import MotionProfile
from domain.shared.value_objects.position_2d import Position2D


class TestAtomicMotionFlyScanExtensions(unittest.TestCase):
    """Test suite for AtomicMotion FlyScan extensions."""

    def setUp(self):
        """Set up common test fixtures."""
        self.profile = MotionProfile(
            min_speed=1.0,  # 1 mm/s
            target_speed=10.0,  # 10 mm/s
            acceleration=5.0,  # 5 mm/s²
            deceleration=5.0  # 5 mm/s²
        )

    def test_get_velocity_at_time_acceleration_phase(self):
        """Test velocity calculation during acceleration phase."""
        motion = AtomicMotion(
            dx=50.0,  # Long motion
            dy=0.0,
            motion_profile=self.profile
        )

        # At t=0: velocity should be min_speed
        v0 = motion.get_velocity_at_time(0.0)
        self.assertAlmostEqual(v0, 1.0, places=2)

        # During acceleration: v = min_speed + acceleration * t
        # At t=1s: v = 1 + 5*1 = 6 mm/s
        v1 = motion.get_velocity_at_time(1.0)
        self.assertAlmostEqual(v1, 6.0, places=2)

        # At t=1.8s (just before target): v = 1 + 5*1.8 = 10 mm/s
        v_target = motion.get_velocity_at_time(1.8)
        self.assertAlmostEqual(v_target, 10.0, places=1)

    def test_get_velocity_at_time_constant_phase(self):
        """Test velocity during constant speed phase."""
        motion = AtomicMotion(
            dx=100.0,  # Very long motion to ensure constant phase exists
            dy=0.0,
            motion_profile=self.profile
        )

        # Acceleration phase: t_acc = (10-1)/5 = 1.8s
        # Should be at target speed after acceleration
        v_constant = motion.get_velocity_at_time(3.0)
        self.assertAlmostEqual(v_constant, 10.0, places=2)

    def test_get_velocity_at_time_deceleration_phase(self):
        """Test velocity during deceleration phase."""
        motion = AtomicMotion(
            dx=100.0,  # Long motion
            dy=0.0,
            motion_profile=self.profile
        )

        # Get velocity near the end (during deceleration)
        # Motion should be decelerating back to min_speed
        # This is harder to calculate exact time, but velocity should be < target_speed
        total_duration = motion.estimated_duration_seconds
        v_near_end = motion.get_velocity_at_time(total_duration - 0.5)

        # Should be somewhere between min and target
        self.assertGreater(v_near_end, 0.0)
        self.assertLess(v_near_end, 10.0)

    def test_get_velocity_at_time_after_completion(self):
        """Test velocity after motion completes."""
        motion = AtomicMotion(
            dx=10.0,
            dy=0.0,
            motion_profile=self.profile
        )

        # After motion completes, velocity should be 0
        v_after = motion.get_velocity_at_time(motion.estimated_duration_seconds + 10.0)
        self.assertEqual(v_after, 0.0)

    def test_get_velocity_at_time_before_start(self):
        """Test velocity before motion starts."""
        motion = AtomicMotion(
            dx=10.0,
            dy=0.0,
            motion_profile=self.profile
        )

        v_before = motion.get_velocity_at_time(-1.0)
        self.assertEqual(v_before, 0.0)

    def test_calculate_acquisition_positions_straight_line_x(self):
        """Test acquisition position calculation for straight X motion."""
        motion = AtomicMotion(
            dx=10.0,  # 10mm in X
            dy=0.0,
            motion_profile=self.profile
        )

        start_pos = Position2D(x=0.0, y=0.0)
        acquisition_rate = 10.0  # 10 Hz

        positions = motion.calculate_acquisition_positions(start_pos, acquisition_rate)

        # Should have several positions
        self.assertGreater(len(positions), 5)

        # First position should be near start
        self.assertAlmostEqual(positions[0].x, 0.0, places=1)
        self.assertAlmostEqual(positions[0].y, 0.0, places=1)

        # Last position should be near end
        self.assertAlmostEqual(positions[-1].x, 10.0, places=1)
        self.assertAlmostEqual(positions[-1].y, 0.0, places=1)

        # All positions should be monotonically increasing in X
        for i in range(1, len(positions)):
            self.assertGreaterEqual(positions[i].x, positions[i-1].x)

    def test_calculate_acquisition_positions_diagonal_motion(self):
        """Test acquisition position calculation for diagonal motion."""
        motion = AtomicMotion(
            dx=10.0,
            dy=10.0,  # 45-degree diagonal
            motion_profile=self.profile
        )

        start_pos = Position2D(x=5.0, y=5.0)
        acquisition_rate = 20.0  # 20 Hz

        positions = motion.calculate_acquisition_positions(start_pos, acquisition_rate)

        # Should have several positions
        self.assertGreater(len(positions), 10)

        # First position should be near start
        self.assertAlmostEqual(positions[0].x, 5.0, places=0)
        self.assertAlmostEqual(positions[0].y, 5.0, places=0)

        # Last position should be near end (15, 15)
        self.assertAlmostEqual(positions[-1].x, 15.0, places=0)
        self.assertAlmostEqual(positions[-1].y, 15.0, places=0)

        # For diagonal motion, X and Y should increase together
        for i in range(1, len(positions)):
            self.assertGreaterEqual(positions[i].x, positions[i-1].x)
            self.assertGreaterEqual(positions[i].y, positions[i-1].y)

    def test_calculate_acquisition_positions_high_rate(self):
        """Test with high acquisition rate produces many positions."""
        motion = AtomicMotion(
            dx=10.0,
            dy=0.0,
            motion_profile=self.profile
        )

        start_pos = Position2D(x=0.0, y=0.0)
        acquisition_rate = 100.0  # 100 Hz

        positions = motion.calculate_acquisition_positions(start_pos, acquisition_rate)

        # At 100 Hz for ~2-3 second motion, should get ~200-300 positions
        self.assertGreater(len(positions), 50)

    def test_calculate_acquisition_positions_low_rate(self):
        """Test with low acquisition rate produces few positions."""
        motion = AtomicMotion(
            dx=10.0,
            dy=0.0,
            motion_profile=self.profile
        )

        start_pos = Position2D(x=0.0, y=0.0)
        acquisition_rate = 1.0  # 1 Hz

        positions = motion.calculate_acquisition_positions(start_pos, acquisition_rate)

        # At 1 Hz for ~2-3 second motion, should get ~2-3 positions
        self.assertGreater(len(positions), 1)
        self.assertLess(len(positions), 10)

    def test_calculate_acquisition_positions_zero_rate(self):
        """Test with zero acquisition rate returns empty list."""
        motion = AtomicMotion(
            dx=10.0,
            dy=0.0,
            motion_profile=self.profile
        )

        start_pos = Position2D(x=0.0, y=0.0)
        positions = motion.calculate_acquisition_positions(start_pos, 0.0)

        self.assertEqual(len(positions), 0)

    def test_calculate_acquisition_positions_zero_motion(self):
        """Test with zero motion returns start position."""
        motion = AtomicMotion(
            dx=0.0,
            dy=0.0,
            motion_profile=self.profile
        )

        start_pos = Position2D(x=5.0, y=10.0)
        positions = motion.calculate_acquisition_positions(start_pos, 100.0)

        # Should return just the start position
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0], start_pos)

    def test_calculate_acquisition_positions_spacing(self):
        """Test that position spacing is reasonable."""
        # Constant speed motion for easier verification
        constant_profile = MotionProfile(
            min_speed=5.0,
            target_speed=5.0,  # Constant
            acceleration=10.0,
            deceleration=10.0
        )

        motion = AtomicMotion(
            dx=50.0,  # 50mm at 5mm/s = 10s
            dy=0.0,
            motion_profile=constant_profile
        )

        start_pos = Position2D(x=0.0, y=0.0)
        acquisition_rate = 10.0  # 10 Hz

        positions = motion.calculate_acquisition_positions(start_pos, acquisition_rate)

        # At constant 5mm/s with 10 Hz: spacing should be ~0.5mm
        # Check spacing between consecutive positions
        if len(positions) > 1:
            for i in range(1, min(5, len(positions))):
                dx = positions[i].x - positions[i-1].x
                # Spacing should be roughly 0.5mm (allowing some variation)
                self.assertGreater(dx, 0.0)
                self.assertLess(dx, 2.0)  # Reasonable upper bound


if __name__ == '__main__':
    unittest.main()
