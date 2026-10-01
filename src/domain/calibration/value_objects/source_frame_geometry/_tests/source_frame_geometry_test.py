import unittest

from domain.calibration.value_objects.source_frame_geometry.source_frame_geometry import SourceFrameGeometry


def make_geometry(positions, ideal):
    return SourceFrameGeometry(
        sphere_positions_m=positions,
        sphere_radii_m=(0.01,) * 4,
        best_fit_square_positions_m=ideal,
        best_fit_square_side_m=0.064,
        distance_residuals_m=(0.0,) * 6,
    )


class TestSourceFrameGeometry(unittest.TestCase):
    def test_square_residuals_are_position_minus_ideal_corner(self):
        ideal = ((-1.0, 1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, -1.0))
        positions = ((-1.0, 1.0), (1.0, -1.0), (1.3, 1.4), (-1.0, -1.0))

        geometry = make_geometry(positions, ideal)

        self.assertAlmostEqual(geometry.square_residuals_m[2][0], 0.3)
        self.assertAlmostEqual(geometry.square_residuals_m[2][1], 0.4)
        self.assertAlmostEqual(geometry.square_rms_residual_m, 0.5 / 2)  # sqrt(0.25 / 4)

    def test_is_immutable(self):
        geometry = make_geometry(((0.0, 0.0),) * 4, ((0.0, 0.0),) * 4)
        with self.assertRaises(Exception):
            geometry.best_fit_square_side_m = 1.0


if __name__ == "__main__":
    unittest.main()
