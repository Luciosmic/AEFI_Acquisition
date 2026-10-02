from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

DEFAULT_N_AVG_VALUES = (1, 2, 4, 8, 16, 32, 64, 96, 127)
DEFAULT_SAMPLES_PER_POINT = 50
# Order of `values_v` / `noise_v_rms`; also the column names of the export.
VALUE_CHANNELS = ("x_in_phase", "y_in_phase", "z_in_phase", "x_quadrature", "y_quadrature", "z_quadrature")


@dataclass(frozen=True)
class AcquisitionThroughputRequestDTO:
    """n_avg values to sweep and samples collected for each."""

    n_avg_values: Tuple[int, ...] = DEFAULT_N_AVG_VALUES
    samples_per_point: int = DEFAULT_SAMPLES_PER_POINT


@dataclass(frozen=True)
class AcquisitionThroughputPointDTO:
    """One n_avg: SI units (s, 1/s, V)."""

    n_avg: int
    sample_period_s: float
    sample_rate_per_s: float
    adc_conversions_per_s: float
    noise_v_rms: Tuple[float, ...]  # x, y, z in-phase, then x, y, z quadrature
    noise_rms_v: float  # quadratic mean of the 6 channels' σ
    noise_in_one_second_v: float


@dataclass(frozen=True)
class AcquisitionThroughputCharacterizationDTO:
    """Result of a sweep. `component_values`: the microcontroller
    characterization quantities it measures, keyed like the component catalog,
    ready to pre-fill the 'Microcontrôleur' tab."""

    points: Tuple[AcquisitionThroughputPointDTO, ...]
    overhead_s: float
    adc_output_rate_hz: Optional[float]
    fit_max_relative_residual: float
    recommended_n_avg: int
    noise_relative_uncertainty: float  # n_avg closer than this in noise in 1 s are not told apart
    oversampling_ratio: int
    excitation: str
    export_path: Optional[str]
    component_values: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AcquisitionThroughputSampleDTO:
    """One raw sample of the sweep, for the export."""

    n_avg: int
    sample_index: int
    timestamp: datetime
    values_v: Tuple[float, ...]  # x, y, z in-phase, then x, y, z quadrature
