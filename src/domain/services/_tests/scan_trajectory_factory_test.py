import unittest

from domain.value_objects.scan.step_scan_config import StepScanConfig
from domain.value_objects.scan.scan_zone import ScanZone
from domain.value_objects.scan.scan_pattern import ScanPattern
from domain.value_objects.scan.scan_axis import ScanAxis
from domain.value_objects.measurement_uncertainty import MeasurementUncertainty
from domain.services.scan_trajectory_factory import ScanTrajectoryFactory


def _base(pattern, axis=ScanAxis.Y):
    return StepScanConfig(
        scan_zone=ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0),
        x_nb_points=3,
        y_nb_points=3,
        scan_pattern=pattern,
        stabilization_delay_ms=100,
        averaging_per_position=1,
        measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=1e-6),
        scan_axis=axis,
    )


class TestScanTrajectoryFactory(unittest.TestCase):

    def test_total_points(self):
        traj = ScanTrajectoryFactory.create_trajectory(_base(ScanPattern.RASTER))
        self.assertEqual(len(traj), 9)

    # --- RASTER ---

    def test_raster_y_axis(self):
        """Default Y-axis: outer=X columns, inner=Y rows (columns-first)."""
        pts = list(ScanTrajectoryFactory.create_trajectory(_base(ScanPattern.RASTER, ScanAxis.Y)))
        # Column x=0: y=0,5,10
        self.assertEqual((pts[0].x, pts[0].y), (0.0, 0.0))
        self.assertEqual((pts[1].x, pts[1].y), (0.0, 5.0))
        self.assertEqual((pts[2].x, pts[2].y), (0.0, 10.0))
        # Column x=5: y=0,5,10
        self.assertEqual((pts[3].x, pts[3].y), (5.0, 0.0))

    def test_raster_x_axis(self):
        """X-axis: outer=Y rows, inner=X columns (rows-first, legacy)."""
        pts = list(ScanTrajectoryFactory.create_trajectory(_base(ScanPattern.RASTER, ScanAxis.X)))
        # Row y=0: x=0,5,10
        self.assertEqual((pts[0].x, pts[0].y), (0.0, 0.0))
        self.assertEqual((pts[1].x, pts[1].y), (5.0, 0.0))
        self.assertEqual((pts[2].x, pts[2].y), (10.0, 0.0))
        # Row y=5: x=0,5,10
        self.assertEqual((pts[3].x, pts[3].y), (0.0, 5.0))

    # --- SERPENTINE ---

    def test_serpentine_y_axis(self):
        """Default Y-axis: zigzag along Y for each X column."""
        pts = list(ScanTrajectoryFactory.create_trajectory(_base(ScanPattern.SERPENTINE, ScanAxis.Y)))
        # Column x=0 (even): y=0,5,10 (bottom→top)
        self.assertEqual((pts[0].x, pts[0].y), (0.0, 0.0))
        self.assertEqual((pts[2].x, pts[2].y), (0.0, 10.0))
        # Column x=5 (odd): y=10,5,0 (top→bottom)
        self.assertEqual((pts[3].x, pts[3].y), (5.0, 10.0))
        self.assertEqual((pts[5].x, pts[5].y), (5.0, 0.0))
        # Column x=10 (even): y=0,5,10
        self.assertEqual((pts[6].x, pts[6].y), (10.0, 0.0))
        self.assertEqual((pts[8].x, pts[8].y), (10.0, 10.0))

    def test_serpentine_x_axis(self):
        """X-axis: zigzag along X for each Y row (legacy)."""
        pts = list(ScanTrajectoryFactory.create_trajectory(_base(ScanPattern.SERPENTINE, ScanAxis.X)))
        # Row y=0 (even): x=0,5,10
        self.assertEqual((pts[0].x, pts[0].y), (0.0, 0.0))
        self.assertEqual((pts[2].x, pts[2].y), (10.0, 0.0))
        # Row y=5 (odd): x=10,5,0
        self.assertEqual((pts[3].x, pts[3].y), (10.0, 5.0))
        self.assertEqual((pts[5].x, pts[5].y), (0.0, 5.0))

    # --- COMB (axis-independent) ---

    def test_comb_trajectory(self):
        """COMB: always Y-first columns regardless of scan_axis."""
        pts = list(ScanTrajectoryFactory.create_trajectory(_base(ScanPattern.COMB)))
        self.assertEqual((pts[0].x, pts[0].y), (0.0, 0.0))
        self.assertEqual((pts[1].x, pts[1].y), (0.0, 5.0))
        self.assertEqual((pts[2].x, pts[2].y), (0.0, 10.0))
        self.assertEqual((pts[3].x, pts[3].y), (5.0, 0.0))


if __name__ == '__main__':
    unittest.main()
