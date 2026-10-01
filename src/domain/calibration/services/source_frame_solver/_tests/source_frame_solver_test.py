import math
import unittest

from domain.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.calibration.errors.source_geometry_inconsistent_error import SourceGeometryInconsistentError
from domain.calibration.services.source_frame_solver.source_frame_solver import SourceFrameSolver
from domain.calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement

# entry order: D_S1_S2, D_S3_S4, D_S1_S3, D_S1_S4, D_S2_S3, D_S2_S4
_PAIRS = ((0, 1), (2, 3), (0, 2), (0, 3), (1, 2), (1, 3))
_QUADRANT_SIGNS = ((-1, 1), (1, -1), (1, 1), (-1, -1))  # S1..S4
_RADIUS_M = 0.01


def make_entry(diameters_m, distances_m) -> SourceGeometryCalibrationEntry:
    return SourceGeometryCalibrationEntry.single(
        sphere_diameters=tuple(CaliperMeasurement.from_resolution(v) for v in diameters_m),
        pairwise_distances_ext=tuple(CaliperMeasurement.from_resolution(v) for v in distances_m),
    )


def entry_from_centers(centers) -> SourceGeometryCalibrationEntry:
    """What a perfect caliper would read on spheres centered at `centers`."""
    distances = [math.dist(centers[i], centers[j]) + 2 * _RADIUS_M for i, j in _PAIRS]
    return make_entry([2 * _RADIUS_M] * 4, distances)


def square_centers(half_side=0.032):
    return [(sx * half_side, sy * half_side) for sx, sy in _QUADRANT_SIGNS]


class TestSourceFrameSolver(unittest.TestCase):
    def test_perfect_square_is_reconstructed_in_its_quadrants_with_zero_defect(self):
        result = SourceFrameSolver.solve(entry_from_centers(square_centers()))

        for actual, expected in zip(result.sphere_positions_m, square_centers()):
            self.assertAlmostEqual(actual[0], expected[0], places=7)
            self.assertAlmostEqual(actual[1], expected[1], places=7)
        self.assertAlmostEqual(result.best_fit_square_side_m, 0.064, places=7)
        self.assertAlmostEqual(result.square_rms_residual_m, 0.0, places=7)
        for residual in result.distance_residuals_m:
            self.assertAlmostEqual(residual, 0.0, places=7)
        self.assertEqual(result.sphere_radii_m, (_RADIUS_M,) * 4)

    def test_perturbed_corner_carries_the_largest_square_residual(self):
        centers = square_centers()
        centers[2] = (centers[2][0] + 0.001, centers[2][1])  # S3 pushed 1mm outward

        result = SourceFrameSolver.solve(entry_from_centers(centers))

        norms = [math.hypot(dx, dy) for dx, dy in result.square_residuals_m]
        self.assertEqual(norms.index(max(norms)), 2)
        self.assertGreater(result.square_rms_residual_m, 1e-4)
        for residual in result.distance_residuals_m:  # still a self-consistent geometry
            self.assertAlmostEqual(residual, 0.0, places=7)

    def test_real_device_measurement_2026_07_24(self):
        """Raw caliper readings from mesures-dgp-pied-a-coulisse-4spheres.md."""
        entry = make_entry(
            [0.0196, 0.0196, 0.0195, 0.0195],
            [0.11142, 0.10908, 0.08436, 0.08352, 0.08230, 0.08450],
        )

        result = SourceFrameSolver.solve(entry)

        for (x, y), (sx, sy) in zip(result.sphere_positions_m, _QUADRANT_SIGNS):
            self.assertGreater(x * sx, 0)
            self.assertGreater(y * sy, 0)
        # S4 is over-determined: noisy real measurements leave a residual
        # (~2e-5 m), distributed by least squares rather than hidden.
        for residual in result.distance_residuals_m:
            self.assertLess(abs(residual), 5e-5)
        self.assertAlmostEqual(result.best_fit_square_side_m, 0.064, delta=0.002)

    def test_result_does_not_depend_on_how_the_bench_is_rotated(self):
        centers = square_centers()
        centers[1] = (centers[1][0] + 0.0005, centers[1][1] - 0.0003)  # S2 defect
        theta = math.radians(17)
        rotated = [
            (x * math.cos(theta) - y * math.sin(theta), x * math.sin(theta) + y * math.cos(theta))
            for x, y in centers
        ]

        straight = SourceFrameSolver.solve(entry_from_centers(centers))
        turned = SourceFrameSolver.solve(entry_from_centers(rotated))

        for a, b in zip(straight.sphere_positions_m, turned.sphere_positions_m):
            self.assertAlmostEqual(a[0], b[0], places=9)
            self.assertAlmostEqual(a[1], b[1], places=9)
        self.assertAlmostEqual(straight.square_rms_residual_m, turned.square_rms_residual_m, places=9)

    def test_inconsistent_symmetric_input_spreads_its_error_symmetrically(self):
        """All sides 85mm, both diagonals 110mm: not a square (the diagonal
        should be ~112.1mm), but nothing distinguishes one sphere from
        another, so the error must not be dumped on the last one solved."""
        entry = make_entry([0.0196] * 4, [0.110, 0.110, 0.085, 0.085, 0.085, 0.085])

        result = SourceFrameSolver.solve(entry)

        self.assertAlmostEqual(result.square_rms_residual_m, 0.0, places=7)
        sides = result.distance_residuals_m[2:]
        for residual in sides:
            self.assertAlmostEqual(residual, sides[0], places=7)
        self.assertAlmostEqual(result.distance_residuals_m[0], result.distance_residuals_m[1], places=7)
        self.assertGreater(abs(result.distance_residuals_m[0]), 5e-4)  # inconsistency stays visible

    def test_open_triangle_s1_s2_s3_is_rejected(self):
        # d12=0.09 but d13=d23=0.02: S3 cannot reach both S1 and S2
        entry = make_entry([0.02] * 4, [0.11, 0.11, 0.04, 0.08, 0.04, 0.08])

        with self.assertRaisesRegex(SourceGeometryInconsistentError, "S1-S2-S3"):
            SourceFrameSolver.solve(entry)


if __name__ == "__main__":
    unittest.main()
