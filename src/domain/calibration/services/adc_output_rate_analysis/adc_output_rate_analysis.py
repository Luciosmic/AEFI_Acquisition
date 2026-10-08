"""
ADC Output Rate Analysis

See adc_output_rate_analysis_intention.md.
"""

from typing import Sequence

import numpy as np

from domain.calibration.value_objects.adc_output_rate_characterization.adc_output_rate_characterization import (
    AdcOutputRateCharacterization,
    AdcOutputRateMeasurement,
)

# Knob, not a law: an interval this far from the median is not a DRDY period.
REGULAR_INTERVAL_TOLERANCE = 0.05


def measure_output_rate(oversampling_ratio: int, falling_edge_times_s: Sequence[float]) -> AdcOutputRateMeasurement:
    edges = np.sort(np.asarray(falling_edge_times_s, dtype=float))
    if edges.size < 2:
        raise ValueError("at least 2 DRDY falling edges are required")
    intervals = np.diff(edges)
    median = float(np.median(intervals))
    regular = intervals[np.abs(intervals - median) <= REGULAR_INTERVAL_TOLERANCE * median]
    if regular.size == 0 or median <= 0:
        raise ValueError("no regular DRDY interval")
    mean = float(regular.mean())
    rate = 1.0 / mean
    return AdcOutputRateMeasurement(
        oversampling_ratio=oversampling_ratio,
        regular_interval_count=int(regular.size),
        irregular_interval_count=int(intervals.size - regular.size),
        median_interval_s=median,
        mean_interval_s=mean,
        interval_std_s=float(regular.std(ddof=1)) if regular.size > 1 else 0.0,
        output_rate_hz=rate,
        implied_modulator_frequency_hz=rate * oversampling_ratio,
    )


def characterize_output_rate(measurements: Sequence[AdcOutputRateMeasurement]) -> AdcOutputRateCharacterization:
    if not measurements:
        raise ValueError("at least one measurement is required")
    ordered = tuple(sorted(measurements, key=lambda m: -m.oversampling_ratio))
    f_mod = np.array([m.implied_modulator_frequency_hz for m in ordered])
    mean = float(f_mod.mean())
    return AdcOutputRateCharacterization(
        measurements=ordered,
        mean_modulator_frequency_hz=mean,
        max_modulator_frequency_relative_deviation=float(np.max(np.abs(f_mod - mean)) / mean),
    )
