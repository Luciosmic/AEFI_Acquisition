import math
import unittest

import numpy as np

from domain.calibration.services.acquisition_throughput_analysis.acquisition_throughput_analysis import (
    characterize_acquisition_throughput,
    characterize_point,
)

OVERHEAD_S = 0.005
ODR_HZ = 1000.0
SIGMA_PER_CONVERSION_V = 1e-5


def synthetic_point(n_avg: int, samples: int = 4000, seed: int = 0):
    """The model the bench is expected to follow: T = T0 + n/ODR, white noise σ0/√n."""
    period = OVERHEAD_S + n_avg / ODR_HZ
    rng = np.random.default_rng(seed + n_avg)
    values = rng.normal(0.0, SIGMA_PER_CONVERSION_V / math.sqrt(n_avg), size=(samples, 6))
    return characterize_point(n_avg, [period] * (samples - 1), values.tolist())


class TestCharacterizePoint(unittest.TestCase):
    def test_rates_follow_the_mean_period(self):
        point = characterize_point(8, [0.010, 0.012, 0.014], [[0.0] * 6, [1.0] * 6])
        self.assertAlmostEqual(point.sample_period_s, 0.012)
        self.assertAlmostEqual(point.sample_rate_per_s, 1 / 0.012)
        self.assertAlmostEqual(point.adc_conversions_per_s, 8 / 0.012)

    def test_noise_per_channel_is_the_sample_standard_deviation(self):
        samples = [[0, 0, 0, 0, 0, 0], [2, 0, 0, 0, 0, 4]]
        point = characterize_point(1, [0.01], samples)
        self.assertAlmostEqual(point.noise_v_rms[0], math.sqrt(2))
        self.assertAlmostEqual(point.noise_v_rms[5], 2 * math.sqrt(2))
        self.assertEqual(point.noise_v_rms[1], 0.0)

    def test_noise_in_one_second_combines_noise_and_period(self):
        """σ·√T: the noise left after averaging the samples of one second."""
        samples = [[1, 1, 1, 1, 1, 1], [-1, -1, -1, -1, -1, -1]]  # σ = √2 on every channel
        point = characterize_point(1, [0.04], samples)
        self.assertAlmostEqual(point.noise_in_one_second_v, math.sqrt(2) * math.sqrt(0.04))

    def test_invalid_inputs_are_refused(self):
        with self.assertRaises(ValueError):
            characterize_point(1, [0.01], [[0.0] * 6])  # one sample: no σ
        with self.assertRaises(ValueError):
            characterize_point(1, [], [[0.0] * 6, [0.0] * 6])  # no period
        with self.assertRaises(ValueError):
            characterize_point(1, [0.0], [[0.0] * 6, [0.0] * 6])  # non-positive period
        with self.assertRaises(ValueError):
            characterize_point(0, [0.01], [[0.0] * 6, [0.0] * 6])


class TestCharacterizeAcquisitionThroughput(unittest.TestCase):
    def test_fit_recovers_overhead_and_adc_output_rate(self):
        result = characterize_acquisition_throughput([synthetic_point(n) for n in (1, 2, 4, 8, 16, 32, 64, 127)])
        self.assertAlmostEqual(result.overhead_s, OVERHEAD_S)
        self.assertAlmostEqual(result.adc_output_rate_hz, ODR_HZ)
        self.assertAlmostEqual(result.fit_max_relative_residual, 0.0, places=9)

    def test_points_are_sorted_by_n_avg(self):
        result = characterize_acquisition_throughput([synthetic_point(n) for n in (32, 1, 8)])
        self.assertEqual([p.n_avg for p in result.points], [1, 8, 32])

    def test_recommends_the_knee_of_the_noise_in_one_second(self):
        """σ√T = σ0·√(T0/n + 1/ODR): falls fast while T0 dominates, then flattens.
        The recommended n_avg is the first one within 5 % of the best."""
        result = characterize_acquisition_throughput([synthetic_point(n) for n in (1, 2, 4, 8, 16, 32, 64, 127)])
        figures = {p.n_avg: p.noise_in_one_second_v for p in result.points}
        best = min(figures.values())
        self.assertLessEqual(figures[result.recommended_n_avg], 1.05 * best)
        smaller = [n for n in figures if n < result.recommended_n_avg]
        self.assertTrue(all(figures[n] > 1.05 * best for n in smaller))
        self.assertIn(result.recommended_n_avg, (32, 64))  # T0 = 5 conversions: the knee is well past 5

    def test_flat_period_gives_no_adc_output_rate(self):
        """The overhead dominates everything: the period does not grow with n_avg."""
        points = [characterize_point(n, [0.05], [[0.0] * 6, [1.0] * 6]) for n in (1, 64)]
        result = characterize_acquisition_throughput(points)
        self.assertIsNone(result.adc_output_rate_hz)
        self.assertAlmostEqual(result.overhead_s, 0.05)

    def test_non_linear_period_shows_in_the_residual(self):
        points = [characterize_point(n, [period], [[0.0] * 6, [1.0] * 6]) for n, period in ((1, 0.01), (8, 0.01), (64, 0.07))]
        self.assertGreater(characterize_acquisition_throughput(points).fit_max_relative_residual, 0.1)

    def test_reports_the_statistical_uncertainty_of_the_noise_estimates(self):
        """σ from N samples is known to 1/√(2(N-1)): 51 samples -> 10 %. The
        worst point sets it (fewest samples)."""
        points = [synthetic_point(1, samples=51), synthetic_point(8, samples=201)]
        self.assertAlmostEqual(characterize_acquisition_throughput(points).noise_relative_uncertainty, 0.1)

    def test_needs_two_distinct_n_avg(self):
        with self.assertRaises(ValueError):
            characterize_acquisition_throughput([synthetic_point(4), synthetic_point(4)])


if __name__ == "__main__":
    unittest.main()
