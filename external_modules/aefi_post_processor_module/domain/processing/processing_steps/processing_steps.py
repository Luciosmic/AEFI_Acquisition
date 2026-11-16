"""
processing_steps - Closed names and order of the processing steps, and their frozen parameters.
See processing_steps_intention.md.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

PREPROCESSED = 'preprocessed'
PHASE_CALIBRATED = 'phase_calibrated'
AMPLITUDE_SUBTRACTED = 'amplitude_subtracted'
ROTATED_FRAME = 'rotated_frame'
INTERPOLATED = 'interpolated'

# Order in which the steps are computed; the closed list of names a processed file may hold.
STEP_NAMES: Tuple[str, ...] = (
    PREPROCESSED,
    PHASE_CALIBRATED,
    AMPLITUDE_SUBTRACTED,
    ROTATED_FRAME,
    INTERPOLATED,
)


def step_index(name: str) -> int:
    """Position of a step in the processing order. Raises ValueError for an unknown name."""
    if name not in STEP_NAMES:
        raise ValueError(f"Unknown processing step '{name}'. Must be one of: {list(STEP_NAMES)}")
    return STEP_NAMES.index(name)


@dataclass(frozen=True)
class ProcessingParameters:
    """Parameters of one processing run. Frozen: a run is replayed with the values it was given."""

    border_width: int = 1
    interpolation_method: str = 'cubic'
    target_grid_size: Optional[int] = None
    reference_point: Tuple[int, int] = (0, 0)
    rotation_angles: Optional[Tuple[float, float, float]] = None  # degrees (theta_x, theta_y, theta_z)
