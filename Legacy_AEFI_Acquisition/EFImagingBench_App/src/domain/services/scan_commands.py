"""
Scan Commands - CQRS Command Side

Commands modify the scan state (start, pause, resume, cancel).
Commands do NOT return data (except command result/acknowledgment).

Responsibility:
- Execute scan operations that change state
- Validate commands before execution
- Emit domain events for state changes

Rationale:
- Separation of concerns (mutation vs query)
- Clear intent (command = action to perform)
- Easier to test and reason about

Design:
- Each command is a separate method
- Commands return CommandResult (success/failure)
- State changes emit events (future: event sourcing)
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from ..ports.i_motion_port import IMotionPort
from ..ports.i_acquisition_port import IAcquisitionPort
from ..value_objects.scan.step_scan_config import StepScanConfig
from ..value_objects.scan.scan_status import ScanStatus
from ..entities.spatial_scan import SpatialScan


@dataclass
class CommandResult:
    """Result of a command execution."""
    success: bool
    message: str
    scan_id: Optional[str] = None  # For execute_scan command


class ScanCommands:
    """
    Command side of scan service (CQRS).
    
    Handles all operations that modify scan state.
    """
    
    def __init__(
        self,
        motion_port: IMotionPort,
        acquisition_port: IAcquisitionPort
    ):
        self._motion_port = motion_port
        self._acquisition_port = acquisition_port
        
        # Scan state (will be moved to aggregate/repository later)
        self._current_scan: Optional[SpatialScan] = None
        self._paused = False
        self._cancelled = False
    
    def execute_scan(self, config: StepScanConfig) -> CommandResult:
        """
        Command: Start a new scan.
        
        Args:
            config: Scan configuration
        
        Returns:
            CommandResult with scan_id if successful
        """
        # Validate
        if self._current_scan is not None:
            return CommandResult(
                success=False,
                message="Cannot start scan: another scan is already running"
            )
        
        validation = self._validate_config(config)
        if not validation.is_valid:
            return CommandResult(
                success=False,
                message=f"Invalid configuration: {validation.errors}"
            )
        
        # Create scan entity
        scan = SpatialScan(
            scan_zone=config.scan_zone,
            start_time=datetime.now(),
            status=ScanStatus.RUNNING
        )
        
        self._current_scan = scan
        self._paused = False
        self._cancelled = False
        
        # TODO: Emit ScanStartedEvent
        
        # Execute scan in background (or return and let application layer handle)
        # For now, execute synchronously
        self._execute_scan_workflow(config)
        
        return CommandResult(
            success=True,
            message="Scan started successfully",
            scan_id=str(id(scan))  # Temporary ID
        )
    
    def pause_scan(self) -> CommandResult:
        """
        Command: Pause the current scan.
        
        Returns:
            CommandResult
        """
        if self._current_scan is None:
            return CommandResult(
                success=False,
                message="No active scan to pause"
            )
        
        if self._paused:
            return CommandResult(
                success=False,
                message="Scan is already paused"
            )
        
        self._paused = True
        # TODO: Emit ScanPausedEvent
        
        return CommandResult(
            success=True,
            message="Scan paused"
        )
    
    def resume_scan(self) -> CommandResult:
        """
        Command: Resume a paused scan.
        
        Returns:
            CommandResult
        """
        if self._current_scan is None:
            return CommandResult(
                success=False,
                message="No active scan to resume"
            )
        
        if not self._paused:
            return CommandResult(
                success=False,
                message="Scan is not paused"
            )
        
        self._paused = False
        # TODO: Emit ScanResumedEvent
        
        return CommandResult(
            success=True,
            message="Scan resumed"
        )
    
    def cancel_scan(self) -> CommandResult:
        """
        Command: Cancel the current scan.
        
        Returns:
            CommandResult
        """
        if self._current_scan is None:
            return CommandResult(
                success=False,
                message="No active scan to cancel"
            )
        
        self._cancelled = True
        # TODO: Emit ScanCancelledEvent
        
        return CommandResult(
            success=True,
            message="Scan cancellation requested"
        )
    
    # Private methods (workflow execution)
    
    def _validate_config(self, config: StepScanConfig):
        """Validate scan configuration."""
        # Import here to avoid circular dependency
        from ..value_objects.validation_result import ValidationResult
        
        errors = []
        
        # Check scan zone
        if config.scan_zone.x_min >= config.scan_zone.x_max:
            errors.append("x_min must be < x_max")
        if config.scan_zone.y_min >= config.scan_zone.y_max:
            errors.append("y_min must be < y_max")
        
        # Check point counts
        if config.x_nb_points < 2:
            errors.append("x_nb_points must be >= 2")
        if config.y_nb_points < 2:
            errors.append("y_nb_points must be >= 2")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def _execute_scan_workflow(self, config: StepScanConfig):
        """Execute the complete scan workflow (internal)."""
        # This will be refactored to use the existing logic
        # from automatic_step_scan_service.py
        pass
