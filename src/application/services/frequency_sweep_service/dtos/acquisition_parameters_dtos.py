"""
Acquisition Parameters DTOs — what a frequency sweep did, in primitives (see
acquisition_parameters_dtos_intention.md). The conditions shared by every
acquisition live in application/shared/acquisition_parameters/.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from application.shared.acquisition_parameters.acquisition_conditions_dtos import (
    AcquisitionConditionsDTO,
    BenchPositionDTO,
    ExportedFileDTO,
    SoftwareProvenanceDTO,
)


@dataclass(frozen=True)
class SweptExcitationDTO:
    """The excitation applied at every frequency: the operator's mode and
    levels, only the frequency swept. `operator_frequency_hz`: set back after."""

    mode: str
    level_s1_s2_percent: float
    level_s3_s4_percent: float
    operator_frequency_hz: float


@dataclass(frozen=True)
class FrequencySweepActivityDTO:
    """One frequency sweep as a PROV activity. `status`: "running" |
    "completed" | "cancelled" | "failed". Fields only known at the end are
    None while running."""

    activity_id: str
    started_at: datetime
    status: str
    role: str
    frequencies_hz: Tuple[float, ...]
    samples_per_frequency: int
    table_height_mm: float
    settle_delay_s: float
    frequency_timeout_s: float
    controller: str
    held_controls: Tuple[str, ...]
    excitation: SweptExcitationDTO
    stream_started_here: bool
    operator_name: str = ""
    operator_id: str = ""
    ended_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    acquired_frequency_count: int = 0
    excitation_restored: Optional[bool] = None
    bench_position_start: Optional[BenchPositionDTO] = None
    bench_position_end: Optional[BenchPositionDTO] = None
    bench_position_unknown_reason: Optional[str] = None
    usb_latency_timer_ms: Optional[float] = None
    usb_latency_unknown_reason: Optional[str] = None


@dataclass(frozen=True)
class FrequencySweepAcquisitionParametersDTO:
    """Everything that influenced one sweep, handed to the export port —
    format-agnostic (the port decides how it is written)."""

    activity: FrequencySweepActivityDTO
    conditions: AcquisitionConditionsDTO
    software: SoftwareProvenanceDTO
    files: Tuple[ExportedFileDTO, ...] = ()
