import unittest
from ...value_objects.scan.step_scan_config import StepScanConfig
from ...value_objects.scan.scan_zone import ScanZone
from ...value_objects.scan.scan_pattern import ScanPattern
from ...value_objects.measurement_uncertainty import MeasurementUncertainty
from ..scan_trajectory_factory import ScanTrajectoryFactory

class TestScanTrajectoryFactory(unittest.TestCase):
    
    def setUp(self):
        self.base_config = StepScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0),
            x_nb_points=3,
            y_nb_points=3,
            scan_pattern=ScanPattern.RASTER,
            stabilization_delay_ms=100,
            averaging_per_position=1,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=1e-6)
        )

    def test_raster_trajectory(self):
        """Test Raster scan mode generation."""
        print("\n=== Testing Raster Trajectory ===")
        config = self.base_config  # Already Raster
        print(f"Config: Mode={config.scan_pattern.name}, Size={config.x_nb_points}x{config.y_nb_points}")
        
        trajectory = ScanTrajectoryFactory.create_trajectory(config)
        print(f"Generated {len(trajectory)} points:")
        points = list(trajectory)
        for i, p in enumerate(points):
            print(f"  [{i}] ({p.x:.1f}, {p.y:.1f})")
        
        self.assertEqual(len(trajectory), 9)
        
        # Check first line (y=0) - Left to Right
        self.assertEqual(points[0].x, 0.0)
        self.assertEqual(points[0].y, 0.0)
        self.assertEqual(points[1].x, 5.0)
        self.assertEqual(points[1].y, 0.0)
        self.assertEqual(points[2].x, 10.0)
        self.assertEqual(points[2].y, 0.0)
        
        # Check second line (y=5) - Left to Right (Raster)
        self.assertEqual(points[3].x, 0.0)
        self.assertEqual(points[3].y, 5.0)
        self.assertEqual(points[5].x, 10.0)

    def test_serpentine_trajectory(self):
        """Test Serpentine scan mode generation."""
        print("\n=== Testing Serpentine Trajectory ===")
        # Create a new config based on base_config but with SERPENTINE mode
        # Since StepScanConfig is frozen, we need to create a new instance
        config = StepScanConfig(
            scan_zone=self.base_config.scan_zone,
            x_nb_points=self.base_config.x_nb_points,
            y_nb_points=self.base_config.y_nb_points,
            scan_pattern=ScanPattern.SERPENTINE,
            stabilization_delay_ms=self.base_config.stabilization_delay_ms,
            averaging_per_position=self.base_config.averaging_per_position,
            measurement_uncertainty=self.base_config.measurement_uncertainty
        )
        print(f"Config: Mode={config.scan_pattern.name}, Size={config.x_nb_points}x{config.y_nb_points}")
        
        trajectory = ScanTrajectoryFactory.create_trajectory(config)
        print(f"Generated {len(trajectory)} points:")
        points = list(trajectory)
        for i, p in enumerate(points):
            print(f"  [{i}] ({p.x:.1f}, {p.y:.1f})")
        
        # First line (y=0): Left -> Right
        self.assertEqual(points[0].x, 0.0)
        self.assertEqual(points[2].x, 10.0)
        
        # Second line (y=5): Right -> Left (Serpentine)
        self.assertEqual(points[3].x, 10.0)
        self.assertEqual(points[3].y, 5.0)
        self.assertEqual(points[4].x, 5.0)
        self.assertEqual(points[5].x, 0.0)
        
        # Third line (y=10): Left -> Right
        self.assertEqual(points[6].x, 0.0)
        self.assertEqual(points[6].y, 10.0)

    def test_comb_trajectory(self):
        """Test Comb scan mode generation."""
        print("\n=== Testing Comb Trajectory ===")
        config = StepScanConfig(
            scan_zone=self.base_config.scan_zone,
            x_nb_points=self.base_config.x_nb_points,
            y_nb_points=self.base_config.y_nb_points,
            scan_pattern=ScanPattern.COMB,
            stabilization_delay_ms=self.base_config.stabilization_delay_ms,
            averaging_per_position=self.base_config.averaging_per_position,
            measurement_uncertainty=self.base_config.measurement_uncertainty
        )
        print(f"Config: Mode={config.scan_pattern.name}, Size={config.x_nb_points}x{config.y_nb_points}")
        
        trajectory = ScanTrajectoryFactory.create_trajectory(config)
        print(f"Generated {len(trajectory)} points:")
        points = list(trajectory)
        for i, p in enumerate(points):
            print(f"  [{i}] ({p.x:.1f}, {p.y:.1f})")
        
        # Column 1 (x=0)
        self.assertEqual(points[0].x, 0.0)
        self.assertEqual(points[0].y, 0.0)
        self.assertEqual(points[1].x, 0.0)
        self.assertEqual(points[1].y, 5.0)
        self.assertEqual(points[2].x, 0.0)
        self.assertEqual(points[2].y, 10.0)
        
        # Column 2 (x=5)
        self.assertEqual(points[3].x, 5.0)
        self.assertEqual(points[3].y, 0.0)

if __name__ == '__main__':
    unittest.main()
