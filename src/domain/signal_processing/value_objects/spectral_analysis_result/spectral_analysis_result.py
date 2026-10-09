"""SpectralAnalysisResult value object (see spectral_analysis_result_intention.md)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Tuple


@dataclass(frozen=True)
class SpectralAnalysisResult:
    """Result of a spectral (FFT) analysis over a time window of corrected field
    samples. Simple value object: its validity is guaranteed by the producing
    service (SpectralAnalysisCalculator), not by an invariant of its own."""

    frequencies_hz: Tuple[float, ...]
    amplitudes_by_channel: Dict[str, Tuple[float, ...]]  # same keys as the time-domain panel
    window_start: datetime
    window_end: datetime
    sample_count: int
