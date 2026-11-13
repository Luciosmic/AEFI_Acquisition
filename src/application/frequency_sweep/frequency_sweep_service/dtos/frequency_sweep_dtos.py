"""
Frequency Sweep DTOs — what crosses the boundary of FrequencySweepService, in
primitives (see frequency_sweep_dtos_intention.md).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

# Order of the 6 values of every measurement tuple (sensor frame, volts).
VALUE_CHANNELS = ("x_in_phase", "y_in_phase", "z_in_phase", "x_quadrature", "y_quadrature", "z_quadrature")

# Stable role identifiers (FrequencySweepRole values) and their operator labels.
ROLE_LABELS = (
    ("instrument_reference", "Référence instrument (table en position basse, sans objet)"),
    ("background", "Fond (table à la hauteur de travail, sans objet)"),
)


@dataclass(frozen=True)
class FrequencySweepRequestDTO:
    """What the operator asks for. `table_height_mm` None = not entered
    (refused); `operator_*` empty = not chosen (exported as such)."""

    role: str = "instrument_reference"
    start_hz: float = 100.0
    stop_hz: float = 10000.0
    frequency_count: int = 21
    samples_per_frequency: int = 50
    table_height_mm: Optional[float] = None
    operator_name: str = ""
    operator_id: str = ""


@dataclass(frozen=True)
class FrequencyPointDTO:
    """One acquired frequency: mean and standard deviation of the 6 values
    (VALUE_CHANNELS order, V), and the phase offset of the synchronous
    detection reference (DDS4 − DDS1) applied at this frequency, None if
    unknown."""

    frequency_index: int
    frequency_hz: float
    samples_count: int
    mean_v: Tuple[float, ...]
    std_v: Tuple[float, ...]
    reference_phase_offset_deg: Optional[float]


@dataclass(frozen=True)
class FrequencySweepSampleDTO:
    """One raw sample kept for a frequency (VALUE_CHANNELS order, V)."""

    frequency_hz: float
    sample_index: int
    timestamp: datetime
    values_v: Tuple[float, ...]


@dataclass(frozen=True)
class FrequencySweepResultDTO:
    """The sweep as it ended. `status`: "completed" | "cancelled" | "failed";
    `points` in grid order (fewer than the grid if not completed)."""

    sweep_id: str
    role: str
    table_height_mm: float
    status: str
    points: Tuple[FrequencyPointDTO, ...]
    export_path: Optional[str]
