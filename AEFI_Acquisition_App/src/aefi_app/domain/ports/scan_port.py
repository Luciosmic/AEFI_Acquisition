from abc import ABC, abstractmethod
from typing import Protocol
from ..entities.spatial_scan import Scan
from ..value_objects import ScanId, ScanResults
from ..value_objects.scan.scan_point_result import ScanPointResult

class ScanObserver(Protocol):
    """Interface for observing scan execution progress.
    
    Follows the Observer pattern to allow the UI (or other listeners)
    to react to scan events without coupling the Domain to the UI.
    """
    
    def on_scan_started(self, scan_id: ScanId) -> None:
        """Called when the scan actually starts execution."""
        ...

    def on_scan_point_acquired(self, scan_id: ScanId, point_index: int, result: ScanPointResult) -> None:
        """Called when a single point is acquired.
        
        Useful for real-time plotting.
        """
        ...

    def on_scan_completed(self, scan_id: ScanId) -> None:
        """Called when the scan finishes successfully."""
        ...

    def on_scan_failed(self, scan_id: ScanId, error: str) -> None:
        """Called when the scan fails."""
        ...
        
    def on_scan_progress(self, scan_id: ScanId, progress: float) -> None:
        """Called to report progress (0.0 to 1.0)."""
        ...


class ScanPort(ABC):
    """Port (Interface) for executing scans.
    
    In Hexagonal Architecture, this is an 'Output Port' (Secondary Port)
    that the Application Layer uses to drive the Infrastructure.
    """

    @abstractmethod
    def execute_scan(self, scan: Scan, observer: ScanObserver) -> ScanResults:
        """Execute the given scan.
        
        This method is blocking (synchronous) from the caller's perspective,
        but implementations might handle it differently. Ideally, it blocks
        until completion to simplify the Application Service logic, while
        the Observer handles real-time feedback.
        
        Parameters
        ----------
        scan : Scan
            The scan entity to execute.
        observer : ScanObserver
            Observer to notify of progress and results.
            
        Returns
        -------
        ScanResults
            The complete results of the scan.
            
        Raises
        ------
        ScanExecutionError
            If the scan fails at the infrastructure level.
        """
        pass
