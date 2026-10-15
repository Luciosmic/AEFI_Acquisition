"""AefiContinuousReadingSampleViewModel (see the plan — section 4).

Responsibility:
- Replace the ad hoc `dict` previously emitted by AefiContinuousReadingPresenter's
  sample_acquired signal with a typed, rendering-oriented view model.

Rationale:
- This is a presenter -> Qt widget detail of rendering, not a presenter -> application
  service boundary (the presenter-boundary standard of this repo targets that
  latter boundary). It therefore lives in interface/view_models/, not
  application/dtos/.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class AefiContinuousReadingSampleViewModel:
    """One corrected AEFI sample (already transformed sensor -> source), ready
    for AefiContinuousReadingPanel to plot."""

    acquisition_id: str
    sample_index: int
    timestamp_iso: str
    ux_in_phase: float
    ux_quadrature: float
    uy_in_phase: float
    uy_quadrature: float
    uz_in_phase: float
    uz_quadrature: float

    def as_channel_dict(self) -> Dict[str, float]:
        """Keys aligned on AefiContinuousReadingPanel.CHANNELS."""
        return {
            "Ux In-Phase": self.ux_in_phase,
            "Ux Quadrature": self.ux_quadrature,
            "Uy In-Phase": self.uy_in_phase,
            "Uy Quadrature": self.uy_quadrature,
            "Uz In-Phase": self.uz_in_phase,
            "Uz Quadrature": self.uz_quadrature,
        }
