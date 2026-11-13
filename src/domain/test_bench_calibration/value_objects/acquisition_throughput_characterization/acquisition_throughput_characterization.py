"""
Acquisition Throughput Characterization Value Objects

See acquisition_throughput_characterization_intention.md.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class AcquisitionThroughputPoint:
    """Throughput and noise of the acquisition chain for one MCU n_avg."""

    n_avg: int
    sample_period_s: float  # mean round-trip per returned sample
    sample_rate_per_s: float  # 1 / sample_period_s
    adc_conversions_per_s: float  # n_avg / sample_period_s: ADC conversions actually used
    noise_v_rms: Tuple[float, ...]  # σ per channel: x, y, z in-phase, then x, y, z quadrature
    noise_rms_v: float  # σ_rms: quadratic mean of the per-channel σ
    noise_in_one_second_v: float  # σ_rms · √period: noise reachable by averaging 1 s
    sample_count: int  # samples the noise was estimated on


@dataclass(frozen=True)
class AcquisitionThroughputCharacterization:
    """Points sorted by n_avg, fitted T(n) = overhead_s + n / adc_output_rate_hz."""

    points: Tuple[AcquisitionThroughputPoint, ...]
    overhead_s: float
    adc_output_rate_hz: Optional[float]  # None: no positive slope (overhead dominates everything)
    fit_max_relative_residual: float  # max |T - T_fit| / T over the points
    recommended_n_avg: int  # smallest n_avg within tolerance of the best noise in 1 s
    # Relative standard uncertainty of the noise estimates (1/√(2(N-1)), worst point):
    # n_avg values closer than this in noise in 1 s are not told apart.
    noise_relative_uncertainty: float
