"""AefiSpectralAnalysisViewModel (see the plan — section 5).

Responsibility:
- Rendering-oriented translation of SpectralAnalysisResult (domain value object,
  tuples) into the lists AefiSpectralAnalysisPanel's pyqtgraph curves expect.

Rationale:
- Same reasoning as AefiContinuousReadingSampleViewModel: a presenter -> Qt
  widget rendering detail, not a presenter -> application service DTO.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class AefiSpectralAnalysisViewModel:
    """One spectral analysis result, ready for AefiSpectralAnalysisPanel to plot."""

    frequencies_hz: List[float]
    amplitudes_by_channel: Dict[str, List[float]]
    window_start_iso: str
    window_end_iso: str
    sample_count: int
