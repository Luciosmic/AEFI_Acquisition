"""
Acquisition Parameters DTOs — the facts a throughput sweep records about its
own conditions, in primitives (see acquisition_parameters_dtos_intention.md).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional, Tuple

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputRequestDTO,
)


# -- conditions read from the system (IAcquisitionConditionsPort) -------------------


@dataclass(frozen=True)
class MountedComponentDTO:
    """The component of one catalog kind mounted on the bench and its current
    characterization. `name` None = nothing mounted. `characterization[key]`:
    a float, a tuple of (x, y) points (curve), or None = not characterized;
    `units[key]` / `curve_x_labels[key]`: as the catalog declares them."""

    kind: str
    name: Optional[str]
    entry_id: Optional[str] = None
    recorded_at: Optional[datetime] = None
    characterization: Mapping[str, Any] = field(default_factory=dict)
    units: Mapping[str, str] = field(default_factory=dict)
    curve_x_labels: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AdcSettingsDTO:
    """ADS131A04 settings applied (physical values, same names as the
    Hardware Advanced Config). `channel_gains[ch]`: digital gain 1..16."""

    oversampling_ratio: int
    clkin_divider: int
    iclk_divider: int
    reference_voltage_v: float
    reference_source: str
    high_resolution: bool
    negative_charge_pump: bool
    channel_gains: Mapping[str, int]
    channel_enabled: Mapping[str, bool]


@dataclass(frozen=True)
class DdsChannelSettingsDTO:
    """One AD9106 DDS channel, raw register codes."""

    gain_code: int
    phase_code: int
    offset_code: int
    constant_code: int
    mode: str


@dataclass(frozen=True)
class SignalGenerationSettingsDTO:
    """AD9106 state as written on the chip (controller memory) — read while
    the excitation is cut, so DDS1/DDS2 gains are 0. Policy flags from the
    resolved configuration (None = unknown)."""

    frequency_hz: float
    channels: Mapping[str, DdsChannelSettingsDTO]
    link_dds1_dds2: Optional[bool] = None
    enforce_dds3_dds4_quadrature: Optional[bool] = None
    link_dds3_dds4_gain: Optional[bool] = None


@dataclass(frozen=True)
class SynchronousDetectionStateDTO:
    compensation_enabled: bool
    phase_calibration_id: Optional[str] = None


@dataclass(frozen=True)
class SensorDeploymentDTO:
    """The sensor's current mounting and the rotation applied to its
    readings. `rotation_origin`: "calibrated" | "trial" | "ideal"."""

    mounting_id: Optional[str]
    mounted_at: Optional[datetime]
    theta_x_degrees: float
    theta_y_degrees: float
    theta_z_degrees: float
    rotation_origin: str
    calibration_id: Optional[str] = None
    calibration_recorded_at: Optional[datetime] = None


@dataclass(frozen=True)
class HostLinkDTO:
    """Serial link host <-> MCU as opened by the driver (None = unknown)."""

    serial_port: Optional[str] = None
    baud_rate: Optional[int] = None


@dataclass(frozen=True)
class AcquisitionConditionsDTO:
    """Everything the system knows about the hardware conditions. A None
    field is unknown; `unknown[field_name]` says why (never silent)."""

    components: Tuple[MountedComponentDTO, ...] = ()
    adc: Optional[AdcSettingsDTO] = None
    signal_generation: Optional[SignalGenerationSettingsDTO] = None
    synchronous_detection: Optional[SynchronousDetectionStateDTO] = None
    sensor_deployment: Optional[SensorDeploymentDTO] = None
    host_link: HostLinkDTO = HostLinkDTO()
    hardware_backends: Mapping[str, str] = field(default_factory=dict)  # subsystem -> "real" | "mock"
    unknown: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class BenchPositionDTO:
    x_mm: float
    y_mm: float


# -- provenance (ISoftwareProvenancePort) ---------------------------------------------


@dataclass(frozen=True)
class SoftwareProvenanceDTO:
    """Code that ran. None = unknown, `unknown_reason` says why."""

    name: str
    version: Optional[str] = None
    commit: Optional[str] = None
    branch: Optional[str] = None
    dirty: Optional[bool] = None
    unknown_reason: Optional[str] = None


# -- files written by the export (IAcquisitionThroughputExportPort) -------------------


@dataclass(frozen=True)
class ExportedFileDTO:
    name: str
    format: str
    byte_size: int
    sha256: str


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
