"""
Scan Application DTOs

Data Transfer Objects for the Scan Application Service.
These objects carry data between the UI/API and the Application Service.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Scan2DConfigDTO:
    """Configuration for a 2D scan (from UI).

    Units: positions in mm, speed in mm/s.
    """
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    x_nb_points: int
    y_nb_points: int
    scan_pattern: str  # 'SERPENTINE', 'RASTER', 'COMB'
    stabilization_delay_ms: int
    averaging_per_position: int
    uncertainty_volts: float
    scan_axis: str = "Y"  # 'Y' (columns-first, default) or 'X' (rows-first)
    motion_speed_mm_s: Optional[float] = None
    differential_mode: bool = False
    differential_settle_delay_ms: float = 50.0
    fly_scan: bool = False  # quick exploration: lines swept in one go, no stop per point


@dataclass(frozen=True)
class LineScanConfigDTO:
    """Configuration for a 1D line scan in the XY plane (from UI).

    Units: mm, degrees. theta=0 -> along X, 90 -> along Y.
    """
    center_x: float
    center_y: float
    length_mm: float
    n_points: int
    theta_deg: float
    stabilization_delay_ms: int
    averaging_per_position: int
    differential_mode: bool = False
    differential_settle_delay_ms: float = 50.0


@dataclass(frozen=True)
class ScanStatusDTO:
    """Status of the current scan."""
    status: str
    is_running: bool
    is_paused: bool
    current_point_index: int
    total_points: int
    progress_percentage: float
    estimated_remaining_seconds: float


@dataclass(frozen=True)
class ExcitationSnapshotDTO:
    """Excitation state at query time (held by the scan for its whole duration)."""
    mode: str
    level_s1_s2_percent: float
    level_s3_s4_percent: float
    frequency_hz: float


@dataclass(frozen=True)
class ScanConfigSnapshotDTO:
    """Configuration of the scan in progress (or last started), read-only.

    `scan_kind` discriminates the shape of `geometry`: "step" (grid: pattern,
    scan_axis, x/y min/max/nb_points) or "line" (center, length_mm, theta_deg,
    start/end). `differential_settle_delay_ms` is the configured value as-is.
    `export_directory` is filled by the caller that knows the export service.
    """
    scan_kind: str
    scan_id: str
    fly_scan: bool
    stabilization_delay_ms: int
    averaging_per_position: int
    differential_mode: bool
    differential_settle_delay_ms: float
    total_points: int
    estimated_duration_s: Optional[float]
    geometry: dict
    excitation: Optional[ExcitationSnapshotDTO] = None
    export_directory: Optional[str] = None
