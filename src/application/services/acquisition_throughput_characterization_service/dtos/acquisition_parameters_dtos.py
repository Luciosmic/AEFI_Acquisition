"""
Acquisition Parameters DTOs — what a throughput sweep did, in primitives (see
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
from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputRequestDTO,
)


# -- what the sweep itself did (recorded by the service) ------------------------------


@dataclass(frozen=True)
class OperatorExcitationDTO:
    """The excitation the operator had set — cut during the sweep, restored after."""

    mode: str
    level_s1_s2_percent: float
    level_s3_s4_percent: float
    frequency_hz: float


@dataclass(frozen=True)
class ExcitationConditionDTO:
    """The excitation condition the sweep applies. `name`: stable identifier
    ("cut"); `label`: as shown to the operator (folder name); `definition`:
    what it means on the hardware."""

    name: str
    label: str
    definition: str


@dataclass(frozen=True)
class ThroughputActivityDTO:
    """One throughput sweep as a PROV activity. `status`: "running" |
    "completed" | "failed". Fields only known at the end are None while
    running."""

    activity_id: str
    started_at: datetime
    status: str
    request: AcquisitionThroughputRequestDTO
    settle_delay_s: float
    sample_timeout_s: float
    excitation_condition: ExcitationConditionDTO
    controller: str
    held_controls: Tuple[str, ...]
    operator_n_avg: int
    operator_excitation: OperatorExcitationDTO
    stream_started_here: bool
    ended_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    n_avg_restored: Optional[bool] = None
    excitation_restored: Optional[bool] = None
    bench_position_start: Optional[BenchPositionDTO] = None
    bench_position_end: Optional[BenchPositionDTO] = None
    bench_position_unknown_reason: Optional[str] = None
    usb_latency_timer_ms: Optional[float] = None
    usb_latency_unknown_reason: Optional[str] = None


@dataclass(frozen=True)
class AcquisitionParametersDTO:
    """Everything that influenced one sweep, handed to the export port —
    format-agnostic (the port decides how it is written)."""

    activity: ThroughputActivityDTO
    conditions: AcquisitionConditionsDTO
    software: SoftwareProvenanceDTO
    files: Tuple[ExportedFileDTO, ...] = ()
