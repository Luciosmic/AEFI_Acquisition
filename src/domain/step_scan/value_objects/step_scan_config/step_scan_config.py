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
from domain.step_scan.value_objects.scan_zone.scan_zone import ScanZone
from domain.step_scan.value_objects.scan_pattern.scan_pattern import ScanPattern
from domain.step_scan.value_objects.scan_axis.scan_axis import ScanAxis
from domain.shared_kernel.value_objects.measurement_uncertainty.measurement_uncertainty import MeasurementUncertainty

@dataclass(frozen=True)
class StepScanConfig:
    """Configuration for a step scan operation.
    
    Defines the complete set of parameters for executing a step scan:
    - Spatial zone to scan
    - Number of points in each direction
    - Scan trajectory pattern
    - Timing parameters
    - Measurement uncertainty requirements
    """
    
    # Spatial configuration
    scan_zone: ScanZone
    x_nb_points: int  # Number of points along X
    y_nb_points: int  # Number of points along Y
    
    # Scan pattern
    scan_pattern: ScanPattern

    # Timing
    stabilization_delay_ms: int  # Wait time after movement

    # Averaging (scan-level, domain logic)
    averaging_per_position: int  # Number of measurements to average per position

    # Measurement quality requirement
    measurement_uncertainty: MeasurementUncertainty

    # Scan orientation â€” must come after all required fields (dataclass constraint)
    scan_axis: ScanAxis = ScanAxis.Y  # fast axis: Y=columns-first (preferred), X=rows-first (legacy)

    # Differential measurement (baseline without excitation + normal measurement)
    differential_mode: bool = False
    # ponytail: 50.0 ms is an unvalidated placeholder — never measured against
    # real hardware (AD9106 gain-register propagation delay, ADS131A04 /
    # synchronous-detection filter settling time both unknown). The real
    # single source of truth is now config_templates/scan_default_config.json
    # (bootstrapped to .aefi_acquisition/configs/, editable via the "Set as
    # default" button in the scan panel) — this literal, and the matching
    # ones in scan_dtos.py/scan_control_panel.py/scan_presenter.py, are only
    # the last-resort fallback used if that config is missing/corrupted, so
    # they're expected to stay in sync with the template's value rather than
    # be collapsed into one Python constant. Ceiling: fine for mock-stack
    # tests, not validated for a real differential scan. Upgrade: once
    # bench-validated on real hardware, update the value here, in the
    # template, and in every fallback site together.
    differential_settle_delay_ms: float = 50.0  # electronic mute settle time, distinct from motor stabilization_delay_ms

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.x_nb_points < 1:
            raise ValueError(f"x_nb_points must be >= 1, got {self.x_nb_points}")

        if self.y_nb_points < 1:
            raise ValueError(f"y_nb_points must be >= 1, got {self.y_nb_points}")

        if self.stabilization_delay_ms < 0:
            raise ValueError(f"stabilization_delay_ms must be >= 0, got {self.stabilization_delay_ms}")

        if self.averaging_per_position < 1:
            raise ValueError(f"averaging_per_position must be >= 1, got {self.averaging_per_position}")

        if self.differential_settle_delay_ms < 0:
            raise ValueError(
                f"differential_settle_delay_ms must be >= 0, got {self.differential_settle_delay_ms}"
            )
    
    def total_points(self) -> int:
        """Calculate total number of scan points."""
        return self.x_nb_points * self.y_nb_points
    
    def validate(self):
        """Validate configuration and return ValidationResult.
        
        Returns:
            ValidationResult with validation status
        """
        from domain.shared_kernel.value_objects.validation_result.validation_result import ValidationResult
        
        # Validation is done in __post_init__, so if we got here, it's valid
        return ValidationResult(is_valid=True, errors=[], warnings=[])
    
    def estimated_duration_seconds(self) -> float:
        """Estimate total scan duration.
        
        Rough estimation based on:
        - Number of points
        - Stabilization delay
        - Acquisition time per point (estimated)
        
        Note: Does not account for movement time (depends on distance and speed).
        """
        # Time per point (stabilization + acquisition)
        stabilization_s = self.stabilization_delay_ms / 1000.0
        
        # Acquisition time per point (rough estimate: 100ms per averaged sample)
        acquisition_s = self.averaging_per_position * 0.1
        
        time_per_point = stabilization_s + acquisition_s
        
        return self.total_points() * time_per_point


