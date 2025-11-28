"""Scan-related value objects (universal and spatial-specific)."""

# Universal scan concepts
from .scan_id import ScanId
from .scan_status import ScanStatus
from .scan_point_result import ScanPointResult
from .scan_results import ScanResults
from .scan_execution_metadata import ScanExecutionMetadata

# Spatial-specific concepts
from .spatial_scan_range import AxisDirection, SpatialRange, ScanAxis

__all__ = [
    # Universal
    "ScanId",
    "ScanStatus",
    "ScanPointResult",
    "ScanResults",
    "ScanExecutionMetadata",
    # Spatial-specific
    "AxisDirection",
    "SpatialRange",
    "ScanAxis",
]
