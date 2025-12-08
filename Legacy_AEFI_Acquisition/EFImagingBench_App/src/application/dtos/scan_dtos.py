"""
Scan Application DTOs

Data Transfer Objects for the Scan Application Service.
These objects carry data between the UI/API and the Application Service.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Scan2DConfigDTO:
    """Configuration for a 2D scan (from UI)."""
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

@dataclass
class ExportConfigDTO:
    """Configuration for data export."""
    enabled: bool
    output_directory: str
    filename_base: str
    include_metadata: bool = True

@dataclass
class ScanStatusDTO:
    """Status of the current scan."""
    status: str
    is_running: bool
    is_paused: bool
    current_point_index: int
    total_points: int
    progress_percentage: float
    estimated_remaining_seconds: float
