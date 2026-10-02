"""
Scan Acquisition Parameters DTOs — what a step scan or a time series did, in
primitives (see scan_acquisition_parameters_dtos_intention.md). The
conditions shared by every acquisition live in application/shared/acquisition_parameters/.
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

STEP_SCAN = "step_scan"
TIME_SERIES = "time_series"


@dataclass(frozen=True)
class StepScanProcedureDTO:
    """The step scan as asked for (StepScanConfig, in primitives)."""

    x_min_mm: float
    x_max_mm: float
    y_min_mm: float
    y_max_mm: float
    x_nb_points: int
    y_nb_points: int
    total_points: int
    pattern: str
    fast_axis: str
    stabilization_delay_ms: float
    averaging_per_position: int
    measurement_uncertainty_v: float
    differential_mode: bool
    differential_settle_delay_ms: float
    estimated_duration_s: float


@dataclass(frozen=True)
class ExcitationStateDTO:
    """The excitation during the acquisition, as the operator set it."""

    mode: str
    level_s1_s2_percent: float
    level_s3_s4_percent: float


@dataclass(frozen=True)
class ElectricFieldProbeDTO:
    """The auxiliary probe connected at acquisition start."""

    brand: str
    model: str
    serial_number: str
    axis_labels: Tuple[str, ...]
    battery_voltage_v: Optional[float] = None
    battery_percentage: Optional[float] = None
    battery_remaining_hours: Optional[float] = None


@dataclass(frozen=True)
class ScanActivityDTO:
    """One scan or time series as a PROV activity. `kind`: STEP_SCAN |
    TIME_SERIES; `status`: "running" | "completed" | "failed" | "cancelled".
    Fields only known at the end are None while running."""

    activity_id: str
    kind: str
    started_at: datetime
    status: str
    excitation: ExcitationStateDTO
    owner: Optional[str]
    held_controls: Tuple[str, ...]
    procedure: Optional[StepScanProcedureDTO] = None
    measured_object: Optional[str] = None  # as typed by the operator at start (None = not described)
    operator: Optional[str] = None
    probe: Optional[ElectricFieldProbeDTO] = None
    bench_position_start: Optional[BenchPositionDTO] = None
    bench_position_end: Optional[BenchPositionDTO] = None
    bench_position_unknown_reason: Optional[str] = None
    usb_latency_timer_ms: Optional[float] = None
    usb_latency_unknown_reason: Optional[str] = None
    ended_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    records_written: Optional[int] = None


@dataclass(frozen=True)
class ScanAcquisitionParametersDTO:
    """Everything that influenced one scan or time series, handed to the export
    port — format-agnostic. `files` is filled by the port when it writes the
    final document (it is the one that knows the files and can hash them)."""

    activity: ScanActivityDTO
    conditions: AcquisitionConditionsDTO
    software: SoftwareProvenanceDTO
    files: Tuple[ExportedFileDTO, ...] = ()
