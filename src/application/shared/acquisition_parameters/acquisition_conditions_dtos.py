"""
Acquisition Conditions DTOs — format-free facts about the conditions of any
acquisition (scan, time series, characterization), shared by every export of
acquisition-parameters.json. See acquisition_conditions_dtos_intention.md.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional, Tuple


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


@dataclass(frozen=True)
class SoftwareProvenanceDTO:
    """Code that ran. None = unknown, `unknown_reason` says why."""

    name: str
    version: Optional[str] = None
    commit: Optional[str] = None
    branch: Optional[str] = None
    dirty: Optional[bool] = None
    unknown_reason: Optional[str] = None


@dataclass(frozen=True)
class ExportedFileDTO:
    name: str
    format: str
    byte_size: int
    sha256: str
