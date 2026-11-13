from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

DEFAULT_PERIODS_PER_CAPTURE = 50


@dataclass(frozen=True)
class AdcOutputRateRequestDTO:
    """Scope channel wired to DRDY, probe ratio, and the OSR values to measure
    (empty: the current OSR only, nothing is changed)."""

    scope_channel: int = 1
    probe_ratio: float = 10.0
    oversampling_ratios: Tuple[int, ...] = ()
    periods_per_capture: int = DEFAULT_PERIODS_PER_CAPTURE


@dataclass(frozen=True)
class DrdyCaptureRequestDTO:
    scope_channel: int
    probe_ratio: float
    window_s: float  # time span to capture


@dataclass(frozen=True)
class DrdyCaptureDTO:
    """One oscilloscope capture of DRDY: falling-edge instants and the raw waveform."""

    falling_edge_times_s: Tuple[float, ...]
    sample_interval_s: float
    instrument: str  # *IDN? of the oscilloscope
    waveform_t_s: Tuple[float, ...] = ()
    waveform_v: Tuple[float, ...] = ()


@dataclass(frozen=True)
class AdcOutputRatePointDTO:
    oversampling_ratio: int
    regular_interval_count: int
    irregular_interval_count: int
    median_interval_s: float
    mean_interval_s: float
    interval_std_s: float
    output_rate_hz: float
    implied_modulator_frequency_hz: float


@dataclass(frozen=True)
class AdcOutputRateCharacterizationDTO:
    """Result. `component_values`: ADC catalog quantities measured, keyed like
    the component catalog, ready to pre-fill the 'ADC' tab."""

    points: Tuple[AdcOutputRatePointDTO, ...]
    mean_modulator_frequency_hz: float
    max_modulator_frequency_relative_deviation: float
    restored_oversampling_ratio: int
    instrument: str
    export_path: Optional[str]
    component_values: Dict[str, Any] = field(default_factory=dict)
