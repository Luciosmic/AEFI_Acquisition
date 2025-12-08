"""
Automatic Step Scan Service - Domain Service

Responsibility:
- Orchestrate automatic step-by-step scanning with acquisition at each point
- Manage scan lifecycle (start, pause, resume, cancel)
- Generate scan trajectories (serpentine, raster, comb)
- Coordinate motion and acquisition via ports

Rationale:
- Pure domain logic, no infrastructure dependencies
- Testable in isolation with mock ports
- Encapsulates complex scan orchestration logic
- Implements business rules for step scanning

Design:
- Domain Service (stateless business logic)
- Hexagonal Architecture: depends on ports (interfaces)
- No Qt, no threads, no files - pure business logic
- Uses dependency injection for ports
"""

from typing import List, Optional
from datetime import datetime
import time

from ..ports.i_motion_port import IMotionPort
from ..ports.i_acquisition_port import IAcquisitionPort
from ..entities.spatial_scan import SpatialScan
from ..value_objects.geometric.position_2d import Position2D
from ..value_objects.acquisition.voltage_measurement import VoltageMeasurement
from ..value_objects.scan.step_scan_config import StepScanConfig
from ..value_objects.scan.measurement_result import MeasurementResult
from ..value_objects.scan.scan_progress import ScanProgress
from ..value_objects.scan.scan_status import ScanStatus
from ..value_objects.scan.scan_mode import ScanMode
from ..value_objects.validation_result import ValidationResult


class AutomaticStepScanService:
    """
    Domain service for automatic step-by-step scanning.
    
    This service orchestrates the complete scan workflow:
    1. Validate configuration
    2. Generate trajectory
    3. For each point: move → stabilize → acquire → average
    4. Manage lifecycle (pause/resume/cancel)
    
    Example:
        >>> motion_port = MotionAdapter(stage_manager)
        >>> acquisition_port = ADS131A04Adapter(communicator)
        >>> service = AutomaticStepScanService(motion_port, acquisition_port)
        >>> 
        >>> config = StepScanConfig(...)
        >>> scan = service.execute_step_scan(config)
        >>> print(f"Scan completed with {len(scan.results)} points")
    """
    
    def __init__(
        self,
        motion_port: IMotionPort,
        acquisition_port: IAcquisitionPort
    ):
        """
        Initialize the scan service with injected ports.
        
        Args:
            motion_port: Port for motion control
            acquisition_port: Port for data acquisition
        """
        self._motion_port = motion_port
        self._acquisition_port = acquisition_port
        self._current_scan: Optional[SpatialScan] = None
        self._paused = False
        self._cancelled = False
    
    # ==========================================
    # Public API
    # ==========================================
    
    def execute_step_scan(self, scan_config: StepScanConfig) -> SpatialScan:
        """
        Execute a complete step scan.
        
        This is the main entry point for running a scan.
        
        Args:
            scan_config: Scan configuration (zone, points, mode, etc.)
        
        Returns:
            SpatialScan entity with all results
        
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If scan fails
        
        Example:
            >>> config = StepScanConfig(
            ...     scan_zone=ScanZone(x_min=0, x_max=100, y_min=0, y_max=100),
            ...     x_nb_points=10,
            ...     y_nb_points=10,
            ...     scan_mode=ScanMode.SERPENTINE,
            ...     stabilization_delay_ms=100,
            ...     averaging_per_scan_point=5,
            ...     measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=10e-6)
            ... )
            >>> scan = service.execute_step_scan(config)
        """
        # 1. Validate configuration
        validation = self._validate_scan_config(scan_config)
        if not validation.is_valid:
            raise ValueError(f"Invalid scan configuration: {validation.errors}")
        
        # 2. Create scan entity
        scan = SpatialScan(
            scan_type=scan_config.scan_mode.value,
            is_fly_scan=False  # Step scan
        )
        self._current_scan = scan
        self._paused = False
        self._cancelled = False
        
        # 3. Generate trajectory
        trajectory = self._generate_scan_trajectory(scan_config)
        
        # 4. Configure acquisition
        self._acquisition_port.configure_for_uncertainty(
            scan_config.measurement_uncertainty
        )
        
        # 5. Start scan
        scan.start()
        
        try:
            # 6. Execute scan points
            for point_index, position in enumerate(trajectory):
                # Check if should continue
                if not self._check_scan_should_continue():
                    if self._cancelled:
                        scan.cancel()
                        return scan
                    # If paused, wait
                    while self._paused and not self._cancelled:
                        time.sleep(0.1)
                    if self._cancelled:
                        scan.cancel()
                        return scan
                
                # Execute single point
                result = self._execute_scan_point(position, scan_config, point_index)
                scan.add_result(result)
            
            # 7. Complete scan
            scan.complete()
            
        except Exception as e:
            scan.fail(str(e))
            raise RuntimeError(f"Scan failed: {e}") from e
        
        finally:
            self._current_scan = None
        
        return scan
    
    def pause_scan(self) -> None:
        """
        Pause the current scan.
        
        The scan will pause after completing the current point.
        Call resume_scan() to continue.
        """
        if self._current_scan and self._current_scan.status == ScanStatus.RUNNING:
            self._paused = True
    
    def resume_scan(self) -> None:
        """Resume a paused scan."""
        self._paused = False
    
    def cancel_scan(self) -> None:
        """
        Cancel the current scan.
        
        The scan will stop after completing the current point.
        """
        if self._current_scan:
            self._cancelled = True
    
    def get_scan_status(self) -> Optional[ScanStatus]:
        """
        Get current scan status.
        
        Returns:
            Current scan status, or None if no active scan
        """
        return self._current_scan.status if self._current_scan else None
    
    def get_scan_progress(self) -> Optional[ScanProgress]:
        """
        Get current scan progress.
        
        Returns:
            Scan progress information, or None if no active scan
        """
        if not self._current_scan:
            return None
        
        # Calculate progress based on results collected
        # This is a simplified version - could be enhanced
        return ScanProgress(
            current_point=len(self._current_scan.results),
            total_points=0,  # Would need to store this
            current_line=0,
            total_lines=0,
            elapsed_time_seconds=0.0,
            estimated_remaining_seconds=0.0
        )
    
    # ==========================================
    # Private Logic
    # ==========================================
    
    def _validate_scan_config(self, config: StepScanConfig) -> ValidationResult:
        """
        Validate scan configuration.
        
        Args:
            config: Configuration to validate
        
        Returns:
            Validation result with errors/warnings
        """
        # Delegate to config's own validation
        return config.validate()
    
    def _generate_scan_trajectory(self, config: StepScanConfig) -> List[Position2D]:
        """
        Generate scan trajectory based on mode.
        
        Args:
            config: Scan configuration
        
        Returns:
            List of positions in scan order
        """
        positions = []
        zone = config.scan_zone
        
        # Calculate step sizes
        x_step = (zone.x_max - zone.x_min) / (config.x_nb_points - 1) if config.x_nb_points > 1 else 0
        y_step = (zone.y_max - zone.y_min) / (config.y_nb_points - 1) if config.y_nb_points > 1 else 0
        
        if config.scan_mode == ScanMode.SERPENTINE:
            # Serpentine: alternating direction on each line
            for j in range(config.y_nb_points):
                y = zone.y_min + j * y_step
                if j % 2 == 0:
                    # Left to right
                    for i in range(config.x_nb_points):
                        x = zone.x_min + i * x_step
                        positions.append(Position2D(x=x, y=y))
                else:
                    # Right to left
                    for i in range(config.x_nb_points - 1, -1, -1):
                        x = zone.x_min + i * x_step
                        positions.append(Position2D(x=x, y=y))
        
        elif config.scan_mode == ScanMode.RASTER:
            # Raster: always left to right
            for j in range(config.y_nb_points):
                y = zone.y_min + j * y_step
                for i in range(config.x_nb_points):
                    x = zone.x_min + i * x_step
                    positions.append(Position2D(x=x, y=y))
        
        elif config.scan_mode == ScanMode.COMB:
            # Comb: scan each column completely before moving to next
            for i in range(config.x_nb_points):
                x = zone.x_min + i * x_step
                for j in range(config.y_nb_points):
                    y = zone.y_min + j * y_step
                    positions.append(Position2D(x=x, y=y))
        
        return positions
    
    def _execute_scan_point(
        self,
        position: Position2D,
        config: StepScanConfig,
        point_index: int
    ) -> dict:
        """
        Execute scan at a single point.
        
        Args:
            position: Target position
            config: Scan configuration
            point_index: Index of this point in trajectory
        
        Returns:
            Measurement result as dict
        """
        # 1. Move to position
        self._move_to_position(position)
        
        # 2. Wait for stabilization
        self._wait_for_stabilization(config.stabilization_delay_ms)
        
        # 3. Acquire measurements
        measurements = self._acquire_measurements(config.averaging_per_scan_point)
        
        # 4. Average measurements
        averaged = self._average_measurements(measurements)
        
        # 5. Create result
        result = {
            'position': {'x': position.x, 'y': position.y},
            'timestamp': datetime.now().isoformat(),
            'voltage': {
                'x_in_phase': averaged.voltage_x_in_phase,
                'x_quadrature': averaged.voltage_x_quadrature,
                'y_in_phase': averaged.voltage_y_in_phase,
                'y_quadrature': averaged.voltage_y_quadrature,
                'z_in_phase': averaged.voltage_z_in_phase,
                'z_quadrature': averaged.voltage_z_quadrature,
            },
            'point_index': point_index,
            'uncertainty_estimate_volts': averaged.uncertainty_estimate_volts
        }
        
        return result
    
    def _move_to_position(self, position: Position2D) -> None:
        """Move to position and wait until stopped."""
        self._motion_port.move_to(position)
        self._motion_port.wait_until_stopped()
    
    def _wait_for_stabilization(self, delay_ms: int) -> None:
        """Wait for mechanical stabilization."""
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)
    
    def _acquire_measurements(self, n_samples: int) -> List[VoltageMeasurement]:
        """
        Acquire N measurement samples.
        
        Each sample is already hardware-averaged by the ADC (OSR).
        
        Args:
            n_samples: Number of samples to acquire
        
        Returns:
            List of voltage measurements
        """
        measurements = []
        for _ in range(n_samples):
            sample = self._acquisition_port.acquire_sample()
            measurements.append(sample)
        return measurements
    
    def _average_measurements(
        self,
        measurements: List[VoltageMeasurement]
    ) -> VoltageMeasurement:
        """
        Average multiple voltage measurements.
        
        This is the domain-level averaging (averaging_per_scan_point).
        Each input measurement is already hardware-averaged (OSR).
        
        Args:
            measurements: List of measurements to average
        
        Returns:
            Averaged voltage measurement
        """
        if not measurements:
            raise ValueError("Cannot average empty list of measurements")
        
        n = len(measurements)
        
        return VoltageMeasurement(
            voltage_x_in_phase=sum(m.voltage_x_in_phase for m in measurements) / n,
            voltage_x_quadrature=sum(m.voltage_x_quadrature for m in measurements) / n,
            voltage_y_in_phase=sum(m.voltage_y_in_phase for m in measurements) / n,
            voltage_y_quadrature=sum(m.voltage_y_quadrature for m in measurements) / n,
            voltage_z_in_phase=sum(m.voltage_z_in_phase for m in measurements) / n,
            voltage_z_quadrature=sum(m.voltage_z_quadrature for m in measurements) / n,
            timestamp=datetime.now(),
            uncertainty_estimate_volts=measurements[0].uncertainty_estimate_volts if measurements else None
        )
    
    def _check_scan_should_continue(self) -> bool:
        """
        Check if scan should continue.
        
        Returns:
            False if paused or cancelled, True otherwise
        """
        return not (self._paused or self._cancelled)
