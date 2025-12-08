"""
Scan Service Facade - CQRS Unified Interface

Provides a unified interface combining Commands and Queries.
This facade delegates to the appropriate CQRS component.

Responsibility:
- Provide single entry point for scan operations
- Delegate to Commands or Queries
- Maintain backward compatibility with existing code

Rationale:
- Easier migration from monolithic service
- Clear separation internally (CQRS)
- Simple API externally (facade)

Design:
- Composition: contains ScanCommands and ScanQueries
- Delegation: forwards calls to appropriate component
- Can be replaced by direct CQRS usage later
"""

from typing import Optional

from ..ports.i_motion_port import IMotionPort
from ..ports.i_acquisition_port import IAcquisitionPort
from ..value_objects.scan.step_scan_config import StepScanConfig
from ..entities.spatial_scan import SpatialScan

from .scan_commands import ScanCommands, CommandResult
from .scan_queries import ScanQueries, ScanStatusDTO, ScanProgressDTO, ScanResultsDTO


class AutomaticStepScanServiceCQRS:
    """
    Facade for scan service using CQRS pattern.
    
    Internally separates Commands (mutations) from Queries (reads).
    Externally provides a unified interface.
    
    Example:
        >>> service = AutomaticStepScanServiceCQRS(motion_port, acquisition_port)
        >>> 
        >>> # Commands (modify state)
        >>> result = service.execute_scan(config)
        >>> service.pause_scan()
        >>> service.resume_scan()
        >>> 
        >>> # Queries (read state)
        >>> status = service.get_scan_status()
        >>> progress = service.get_scan_progress()
    """
    
    def __init__(
        self,
        motion_port: IMotionPort,
        acquisition_port: IAcquisitionPort
    ):
        """
        Initialize scan service with CQRS architecture.
        
        Args:
            motion_port: Port for motion control
            acquisition_port: Port for data acquisition
        """
        # Command side (write model)
        self._commands = ScanCommands(motion_port, acquisition_port)
        
        # Query side (read model)
        # For now, queries read from command side state
        # Later: can use separate read model / projections
        self._queries = ScanQueries(self._commands)
    
    # === Commands (modify state) ===
    
    def execute_scan(self, config: StepScanConfig) -> CommandResult:
        """
        Execute a complete step scan.
        
        This is a COMMAND - it modifies state.
        
        Args:
            config: Scan configuration
        
        Returns:
            CommandResult with success/failure and scan_id
        """
        return self._commands.execute_scan(config)
    
    def pause_scan(self) -> CommandResult:
        """
        Pause the current scan.
        
        This is a COMMAND - it modifies state.
        
        Returns:
            CommandResult
        """
        return self._commands.pause_scan()
    
    def resume_scan(self) -> CommandResult:
        """
        Resume a paused scan.
        
        This is a COMMAND - it modifies state.
        
        Returns:
            CommandResult
        """
        return self._commands.resume_scan()
    
    def cancel_scan(self) -> CommandResult:
        """
        Cancel the current scan.
        
        This is a COMMAND - it modifies state.
        
        Returns:
            CommandResult
        """
        return self._commands.cancel_scan()
    
    # === Queries (read state) ===
    
    def get_scan_status(self) -> Optional[ScanStatusDTO]:
        """
        Get current scan status.
        
        This is a QUERY - it only reads state.
        
        Returns:
            ScanStatusDTO if scan exists, None otherwise
        """
        return self._queries.get_scan_status()
    
    def get_scan_progress(self) -> Optional[ScanProgressDTO]:
        """
        Get current scan progress.
        
        This is a QUERY - it only reads state.
        
        Returns:
            ScanProgressDTO if scan exists, None otherwise
        """
        return self._queries.get_scan_progress()
    
    def get_scan_results(self) -> Optional[ScanResultsDTO]:
        """
        Get scan results.
        
        This is a QUERY - it only reads state.
        
        Returns:
            ScanResultsDTO if scan exists, None otherwise
        """
        return self._queries.get_scan_results()
    
    # === Backward compatibility ===
    
    def execute_step_scan(self, config: StepScanConfig) -> SpatialScan:
        """
        Legacy method for backward compatibility.
        
        Executes scan and returns SpatialScan entity.
        New code should use execute_scan() which returns CommandResult.
        
        Args:
            config: Scan configuration
        
        Returns:
            SpatialScan entity
        
        Raises:
            ValueError: If scan execution fails
        """
        result = self.execute_scan(config)
        
        if not result.success:
            raise ValueError(result.message)
        
        # Return the scan entity (for backward compatibility)
        return self._commands._current_scan
