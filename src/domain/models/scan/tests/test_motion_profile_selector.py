"""
Unit tests for MotionProfileSelector service.
"""

import unittest
from domain.models.scan.services.motion_profile_selector import MotionProfileSelector
from domain.models.test_bench.value_objects.motion_profile import MotionProfile


class TestMotionProfileSelector(unittest.TestCase):
    """Test suite for MotionProfileSelector service."""
    
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
    
    def test_default_selector(self):
        """Test selector with default profiles."""
        selector = MotionProfileSelector()
        
        # Small distance should use slow profile
        profile = selector.select_for_distance(2.0)
        self.assertEqual(profile, selector.slow_profile)
        
        # Large distance should use fast profile
        profile = selector.select_for_distance(10.0)
        self.assertEqual(profile, selector.fast_profile)
    
    def test_custom_threshold(self):
        """Test selector with custom threshold."""
        selector = MotionProfileSelector(small_distance_threshold_mm=10.0)
        
        # Below threshold
        profile = selector.select_for_distance(5.0)
        self.assertEqual(profile, selector.slow_profile)
        
        # At threshold (should use fast)
        profile = selector.select_for_distance(10.0)
        self.assertEqual(profile, selector.fast_profile)
        
        # Above threshold
        profile = selector.select_for_distance(15.0)
        self.assertEqual(profile, selector.fast_profile)
    
    def test_custom_profiles(self):
        """Test selector with custom profiles."""
        custom_slow = MotionProfile(
            min_speed=0.05,
            target_speed=0.5,
            acceleration=0.2,
            deceleration=0.2,
        )
        custom_fast = MotionProfile(
            min_speed=1.0,
            target_speed=20.0,
            acceleration=10.0,
            deceleration=10.0,
        )
        
        selector = MotionProfileSelector(
            small_distance_threshold_mm=5.0,
            slow_profile=custom_slow,
            fast_profile=custom_fast,
        )
        
        # Small distance
        profile = selector.select_for_distance(2.0)
        self.assertEqual(profile, custom_slow)
        
        # Large distance
        profile = selector.select_for_distance(10.0)
        self.assertEqual(profile, custom_fast)
    
    def test_boundary_conditions(self):
        """Test boundary conditions."""
        selector = MotionProfileSelector(small_distance_threshold_mm=5.0)
        
        # Just below threshold
        profile = selector.select_for_distance(4.999)
        self.assertEqual(profile, selector.slow_profile)
        
        # Exactly at threshold
        profile = selector.select_for_distance(5.0)
        self.assertEqual(profile, selector.fast_profile)
        
        # Just above threshold
        profile = selector.select_for_distance(5.001)
        self.assertEqual(profile, selector.fast_profile)
    
    def test_zero_distance(self):
        """Test zero distance."""
        selector = MotionProfileSelector()
        
        # Zero distance should use slow profile (below threshold)
        profile = selector.select_for_distance(0.0)
        self.assertEqual(profile, selector.slow_profile)
    
    def test_very_large_distance(self):
        """Test very large distance."""
        selector = MotionProfileSelector()
        
        # Very large distance should use fast profile
        profile = selector.select_for_distance(1000.0)
        self.assertEqual(profile, selector.fast_profile)


if __name__ == '__main__':
    unittest.main()

