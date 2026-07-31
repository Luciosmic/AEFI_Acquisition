import random
import unittest

from infrastructure.mocks.cube_sensor_field_simulator import CubeSensorFieldSimulator
from infrastructure.mocks._tests.point_charge_field_simulator_test import make_synthetic_config


class TestCubeSensorFieldSimulator(unittest.TestCase):
    def test_zero_level_gives_zero_voltages(self):
        sim = CubeSensorFieldSimulator.from_config(make_synthetic_config())
        vx, vy, vz = sim.compute_axis_voltages(0.0, 0.0)
        self.assertAlmostEqual(vx, 0.0)
        self.assertAlmostEqual(vy, 0.0)
        self.assertAlmostEqual(vz, 0.0)

    def test_no_rotation_gives_zero_z_by_symmetry(self):
        # Sensor unrotated (identity, per make_synthetic_config) and coplanar
        # with the spheres -> no z asymmetry to pick up.
        sim = CubeSensorFieldSimulator.from_config(make_synthetic_config())
        vx, vy, vz = sim.compute_axis_voltages(100.0, 0.0)
        self.assertAlmostEqual(vz, 0.0, places=9)

    def test_s1_s2_only_produces_nonzero_x_and_y_unrotated(self):
        sim = CubeSensorFieldSimulator.from_config(make_synthetic_config())
        vx, vy, vz = sim.compute_axis_voltages(100.0, 0.0)
        self.assertNotAlmostEqual(vx, 0.0)
        self.assertNotAlmostEqual(vy, 0.0)

    def test_level_scales_linearly(self):
        sim = CubeSensorFieldSimulator.from_config(make_synthetic_config())
        full = sim.compute_axis_voltages(100.0, 0.0)
        half = sim.compute_axis_voltages(50.0, 0.0)
        for f, h in zip(full, half):
            self.assertAlmostEqual(h, f / 2.0, places=9)

    def test_rotation_moves_signal_into_z(self):
        config = make_synthetic_config()
        config["sensor"]["calibration"]["sensor_to_lab_rotation"] = {
            "theta_x": 90.0, "theta_y": 0.0, "theta_z": 0.0,
        }
        sim = CubeSensorFieldSimulator.from_config(config)
        vx, vy, vz = sim.compute_axis_voltages(100.0, 0.0)
        # A 90 deg rotation about X swaps the source-frame y/z roles for the
        # sensor's local axes -> the y-signal from the unrotated case should
        # now show up (at least partly) on z instead.
        self.assertNotAlmostEqual(vz, 0.0)

    def test_finite_face_average_converges_toward_point_value_for_tiny_cube(self):
        """Sanity check: a near-zero-size cube should behave like the old
        point-sensor model (field ~ finite difference over a tiny gap)."""
        big_config = make_synthetic_config(dimension_m=0.008)
        tiny_config = make_synthetic_config(dimension_m=0.0001)
        big = CubeSensorFieldSimulator.from_config(big_config).compute_axis_voltages(100.0, 0.0)
        tiny = CubeSensorFieldSimulator.from_config(tiny_config).compute_axis_voltages(100.0, 0.0)
        # Both should be same order of magnitude and same sign pattern —
        # finite-size averaging shouldn't flip signs for a mild geometry.
        for b, t in zip(big, tiny):
            self.assertEqual(b > 0, t > 0)

    def test_default_is_deterministic_across_calls(self):
        sim = CubeSensorFieldSimulator.from_config(make_synthetic_config())
        first = sim.compute_axis_voltages(80.0, 80.0)
        second = sim.compute_axis_voltages(80.0, 80.0)
        self.assertEqual(first, second)

    def test_sensor_noise_varies_across_calls(self):
        sim = CubeSensorFieldSimulator.from_config(
            make_synthetic_config(), sensor_noise_std_v=0.001, rng=random.Random(1)
        )
        first = sim.compute_axis_voltages(0.0, 0.0)  # no field -> pure noise
        second = sim.compute_axis_voltages(0.0, 0.0)
        self.assertNotEqual(first, second)

    def test_source_noise_varies_across_calls(self):
        sim = CubeSensorFieldSimulator.from_config(
            make_synthetic_config(), source_level_noise_std_percent=5.0, rng=random.Random(1)
        )
        first = sim.compute_axis_voltages(100.0, 0.0)
        second = sim.compute_axis_voltages(100.0, 0.0)
        self.assertNotEqual(first, second)

    def test_seeded_rng_is_reproducible(self):
        sim_a = CubeSensorFieldSimulator.from_config(
            make_synthetic_config(), sensor_noise_std_v=0.001, rng=random.Random(42)
        )
        sim_b = CubeSensorFieldSimulator.from_config(
            make_synthetic_config(), sensor_noise_std_v=0.001, rng=random.Random(42)
        )
        self.assertEqual(sim_a.compute_axis_voltages(50.0, 50.0), sim_b.compute_axis_voltages(50.0, 50.0))

    def test_from_default_config_has_nonzero_noise_by_default(self):
        sim = CubeSensorFieldSimulator.from_default_config()
        self.assertGreater(sim._source_level_noise_std_percent, 0.0)
        self.assertGreater(sim._sensor_noise_std_v, 0.0)


if __name__ == "__main__":
    unittest.main()
