import unittest

import numpy as np

from domain.calibration.services.adc_output_rate_analysis.adc_output_rate_analysis import (
    characterize_output_rate,
    measure_output_rate,
)

F_MOD_HZ = 4.096e6


def drdy_edges(osr, count=50, jitter_s=0.0, seed=0):
    period = osr / F_MOD_HZ
    rng = np.random.default_rng(seed)
    return np.arange(count) * period + rng.normal(0.0, jitter_s, count)


class TestMeasureOutputRate(unittest.TestCase):
    def test_regular_edges_give_the_output_rate_and_the_modulator_frequency(self):
        m = measure_output_rate(4096, drdy_edges(4096))
        self.assertAlmostEqual(m.output_rate_hz, 1000.0, places=6)
        self.assertAlmostEqual(m.implied_modulator_frequency_hz, F_MOD_HZ, delta=1e-3)
        self.assertEqual((m.regular_interval_count, m.irregular_interval_count), (49, 0))
        self.assertAlmostEqual(m.interval_std_s, 0.0)

    def test_a_pause_is_counted_apart_not_averaged(self):
        """A missing pulse makes one 2-period interval: not a period."""
        edges = np.delete(drdy_edges(4096), 10)
        m = measure_output_rate(4096, edges)
        self.assertEqual((m.regular_interval_count, m.irregular_interval_count), (47, 1))
        self.assertAlmostEqual(m.output_rate_hz, 1000.0, places=6)

    def test_jitter_shows_in_the_standard_deviation(self):
        m = measure_output_rate(4096, drdy_edges(4096, count=400, jitter_s=2e-7))
        self.assertAlmostEqual(m.interval_std_s, 2e-7 * np.sqrt(2), delta=0.3e-7)
        self.assertAlmostEqual(m.output_rate_hz, 1000.0, delta=0.05)

    def test_too_few_edges_are_refused(self):
        with self.assertRaises(ValueError):
            measure_output_rate(4096, [0.0])


class TestCharacterizeOutputRate(unittest.TestCase):
    def test_osr_applied_gives_one_modulator_frequency(self):
        result = characterize_output_rate([measure_output_rate(osr, drdy_edges(osr)) for osr in (32, 4096, 512)])
        self.assertEqual([m.oversampling_ratio for m in result.measurements], [4096, 512, 32])
        self.assertAlmostEqual(result.mean_modulator_frequency_hz, F_MOD_HZ, delta=1e-2)
        self.assertLess(result.max_modulator_frequency_relative_deviation, 1e-9)

    def test_an_osr_not_applied_shows_as_a_deviation(self):
        """The register says 512 but the ADC still runs at 4096: f_MOD implied is off by 8x."""
        stuck = measure_output_rate(512, drdy_edges(4096))
        result = characterize_output_rate([measure_output_rate(4096, drdy_edges(4096)), stuck])
        self.assertGreater(result.max_modulator_frequency_relative_deviation, 0.5)


if __name__ == "__main__":
    unittest.main()
