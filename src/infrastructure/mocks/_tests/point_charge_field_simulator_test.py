import math
import unittest

import numpy as np

from infrastructure.mocks.point_charge_field_simulator import PointChargeFieldSimulator, VOLTS_PER_PERCENT


def make_synthetic_config(
    diagonal_m: float = 0.09,
    radius_m: float = 0.0098,
    gain: float = 63600.0,
    dimension_m: float = 0.008,
) -> dict:
    """A perfect-square config with known values, so expected results are hand-computable."""
    diam = 2 * radius_m
    return {
        "excitation": {
            "sources_geometry": {
                "sphere_diameters": {s: {"value": diam} for s in ("S1", "S2", "S3", "S4")},
                "pairwise_distances_ext": {
                    "D_S1_S2": {"value": diagonal_m + diam},
                    "D_S3_S4": {"value": diagonal_m + diam},
                },
            }
        },
        "sensor": {
            "dimension": {"value": dimension_m},
            "calibration": {
                "gain": {"value": gain},
                "sensor_to_lab_rotation": {"theta_x": 0.0, "theta_y": 0.0, "theta_z": 0.0},
            },
        },
    }


class TestPointChargeFieldSimulator(unittest.TestCase):
    def test_zero_level_gives_zero_potential_everywhere(self):
        sim = PointChargeFieldSimulator.from_config(make_synthetic_config())
        self.assertAlmostEqual(sim.potential_at(np.zeros(3), 0.0, 0.0), 0.0)
        self.assertAlmostEqual(sim.potential_at(np.array([0.01, 0.01, 0.0]), 0.0, 0.0), 0.0)

    def test_potential_at_center_matches_hand_computation(self):
        diagonal, radius = 0.09, 0.0098
        sim = PointChargeFieldSimulator.from_config(make_synthetic_config(diagonal, radius))
        r_center = diagonal / 2.0
        v0 = 100.0 * VOLTS_PER_PERCENT

        # S1 (sign -1) and S2 (sign +1) both at distance r_center: potentials
        # of opposite sign, don't cancel in general (V is a scalar, and this
        # is a single point) — total = (-v0 + v0) * radius / r_center = 0
        # only because S1/S2 magnitudes are identical; verify directly.
        total = sim.potential_at(np.zeros(3), 100.0, 0.0)
        expected = (-v0 * radius / r_center) + (v0 * radius / r_center)
        self.assertAlmostEqual(total, expected)
        self.assertAlmostEqual(total, 0.0)  # equal & opposite at equal distance

    def test_potential_is_nonzero_off_center(self):
        sim = PointChargeFieldSimulator.from_config(make_synthetic_config())
        # Off-center point breaks the equidistance symmetry.
        total = sim.potential_at(np.array([0.005, 0.0, 0.0]), 100.0, 0.0)
        self.assertNotAlmostEqual(total, 0.0)

    def test_level_scales_potential_linearly(self):
        sim = PointChargeFieldSimulator.from_config(make_synthetic_config())
        point = np.array([0.005, 0.002, 0.001])
        full = sim.potential_at(point, 100.0, 0.0)
        half = sim.potential_at(point, 50.0, 0.0)
        self.assertAlmostEqual(half, full / 2.0, places=9)

    def test_potential_grows_near_a_sphere_surface(self):
        diagonal, radius = 0.09, 0.0098
        sim = PointChargeFieldSimulator.from_config(make_synthetic_config(diagonal, radius))
        r_center = diagonal / 2.0
        s1_direction = np.array([-1.0, 1.0, 0.0]) / math.sqrt(2.0)
        s1_position = r_center * s1_direction
        near_s1 = s1_position + s1_direction * (radius * 1.01)  # just outside its surface
        far_point = np.array([0.2, 0.2, 0.2])  # far from every sphere

        near_potential = sim.potential_at(near_s1, 100.0, 0.0)
        far_potential = sim.potential_at(far_point, 100.0, 0.0)
        self.assertGreater(abs(near_potential), abs(far_potential) * 10)


if __name__ == "__main__":
    unittest.main()
