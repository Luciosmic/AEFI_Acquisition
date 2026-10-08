"""
Acquisition Throughput Analysis

See acquisition_throughput_analysis_intention.md.
"""

import math
from typing import Sequence

import numpy as np

from domain.calibration.value_objects.acquisition_throughput_characterization.acquisition_throughput_characterization import (
    AcquisitionThroughputCharacterization,
    AcquisitionThroughputPoint,
)

# Knob, not a law: a larger n_avg only slows the output rate once its noise
# in 1 s is within this fraction of the best one.
NOISE_IN_ONE_SECOND_TOLERANCE = 0.05
# Below this share of the period at the largest n_avg, the slope is timing
# jitter, not the ADC: no ADC output rate is reported.
MIN_RESOLVABLE_SLOPE_SHARE = 0.01


def characterize_point(
    n_avg: int, sample_periods_s: Sequence[float], channel_samples_v: Sequence[Sequence[float]]
) -> AcquisitionThroughputPoint:
    """`sample_periods_s`: round-trip of each returned sample (timestamp
    differences of consecutive samples); `channel_samples_v`: one row of 6
    channel voltages per sample."""
    if n_avg < 1:
        raise ValueError(f"n_avg must be >= 1, got {n_avg}")
    periods = np.asarray(sample_periods_s, dtype=float)
    values = np.asarray(channel_samples_v, dtype=float)
    if periods.size == 0 or np.any(periods <= 0):
        raise ValueError("at least one positive sample period is required")
    if values.ndim != 2 or values.shape[0] < 2:
        raise ValueError("at least 2 samples are required to estimate the noise")

    period = float(periods.mean())
    noise = values.std(axis=0, ddof=1)
    noise_rms = float(np.sqrt(np.mean(noise ** 2)))
    return AcquisitionThroughputPoint(
        n_avg=n_avg,
        sample_period_s=period,
        sample_rate_per_s=1.0 / period,
        adc_conversions_per_s=n_avg / period,
        noise_v_rms=tuple(float(s) for s in noise),
        noise_rms_v=noise_rms,
        noise_in_one_second_v=noise_rms * math.sqrt(period),
        sample_count=int(values.shape[0]),
    )


def characterize_acquisition_throughput(
    points: Sequence[AcquisitionThroughputPoint],
) -> AcquisitionThroughputCharacterization:
    ordered = tuple(sorted(points, key=lambda p: p.n_avg))
    n = np.array([p.n_avg for p in ordered], dtype=float)
    period = np.array([p.sample_period_s for p in ordered])
    if len(set(n)) < 2:
        raise ValueError("at least 2 distinct n_avg values are required to fit T(n) = T0 + n/ODR")

    slope, overhead = np.polyfit(n, period, 1)
    residual = np.abs(period - (overhead + slope * n)) / period
    slope_resolved = slope * n.max() >= MIN_RESOLVABLE_SLOPE_SHARE * period[-1]

    best = min(p.noise_in_one_second_v for p in ordered)
    recommended = next(
        p.n_avg for p in ordered if p.noise_in_one_second_v <= (1.0 + NOISE_IN_ONE_SECOND_TOLERANCE) * best
    )
    return AcquisitionThroughputCharacterization(
        points=ordered,
        overhead_s=float(overhead),
        adc_output_rate_hz=float(1.0 / slope) if slope_resolved else None,
        fit_max_relative_residual=float(residual.max()),
        recommended_n_avg=recommended,
        noise_relative_uncertainty=max(1.0 / math.sqrt(2 * (p.sample_count - 1)) for p in ordered),
    )
