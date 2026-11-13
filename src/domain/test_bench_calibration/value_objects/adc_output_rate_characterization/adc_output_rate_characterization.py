"""
ADC Output Rate Characterization Value Objects

See adc_output_rate_characterization_intention.md.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class AdcOutputRateMeasurement:
    """ODR of the ADC at one OSR, from the DRDY falling edges."""

    oversampling_ratio: int
    regular_interval_count: int  # intervals within tolerance of the median: periods
    irregular_interval_count: int  # longer/shorter intervals (pause, missed pulse): not periods
    median_interval_s: float
    mean_interval_s: float  # over the regular intervals
    interval_std_s: float  # over the regular intervals
    output_rate_hz: float  # 1 / mean_interval_s
    implied_modulator_frequency_hz: float  # output_rate_hz * oversampling_ratio


@dataclass(frozen=True)
class AdcOutputRateCharacterization:
    """Measurements sorted by decreasing OSR; consistency of f_MOD across them."""

    measurements: Tuple[AdcOutputRateMeasurement, ...]
    mean_modulator_frequency_hz: float
    max_modulator_frequency_relative_deviation: float  # max |f_MOD_i - mean| / mean
