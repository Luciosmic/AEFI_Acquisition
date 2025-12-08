"""
Domain: Step Scan Configuration

Responsibility:
    Complete configuration for a step scan operation.

Rationale:
    Encapsulates all parameters needed to execute a step scan.
    Immutable value object with validation.

Design:
    - Frozen dataclass (immutable)
    - Validates all parameters in __post_init__
    - Provides derived calculations (total_points, estimated_duration)
"""
from dataclasses import dataclass
from .scan_zone import ScanZone
from .scan_mode import ScanMode
from ..acquisition.acquisition_parameters import AcquisitionParameters

@dataclass(frozen=True)
class StepScanConfig:
    """Configuration for a step scan operation.
    
    Defines the complete set of parameters for executing a step scan:
    - Spatial zone to scan
    - Number of points in each direction
    - Scan trajectory pattern
    - Timing parameters
    - Acquisition parameters
    """
    
    # Spatial configuration
    scan_zone: ScanZone
    x_nb_points: int  # Number of points along X
    y_nb_points: int  # Number of points along Y
    
    # Scan pattern
    scan_mode: ScanMode
    
    # Timing
    stabilization_delay_ms: int  # Wait time after movement
    
    # Averaging (scan-level, domain logic)
    averaging_per_scan_point: int  # Number of measurements to average per point
    
    # Device configuration
    acquisition_params: AcquisitionParameters
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.x_nb_points < 1:
            raise ValueError(f"x_nb_points must be >= 1, got {self.x_nb_points}")
        
        if self.y_nb_points < 1:
            raise ValueError(f"y_nb_points must be >= 1, got {self.y_nb_points}")
        
        if self.stabilization_delay_ms < 0:
            raise ValueError(f"stabilization_delay_ms must be >= 0, got {self.stabilization_delay_ms}")
        
        if self.averaging_per_scan_point < 1:
            raise ValueError(f"averaging_per_scan_point must be >= 1, got {self.averaging_per_scan_point}")
    
    def total_points(self) -> int:
        """Calculate total number of scan points."""
        return self.x_nb_points * self.y_nb_points
    
    def estimated_duration_seconds(self) -> float:
        """Estimate total scan duration.
        
        Rough estimation based on:
        - Number of points
        - Stabilization delay
        - Acquisition time per point
        
        Note: Does not account for movement time (depends on distance and speed).
        """
        # Time per point (stabilization + acquisition)
        stabilization_s = self.stabilization_delay_ms / 1000.0
        
        # Acquisition time per point (rough estimate)
        # averaging_per_scan_point measurements at sampling_rate
        acquisition_s = self.averaging_per_scan_point / self.acquisition_params.sampling_rate
        
        time_per_point = stabilization_s + acquisition_s
        
        return self.total_points() * time_per_point

