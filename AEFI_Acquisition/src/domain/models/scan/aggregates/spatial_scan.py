"""
Domain: Scan

Responsibility:
    Represents a spatial scan entity with its lifecycle and configuration.

Rationale:
    Encapsulates scan identity, mode, status, and results.
    Manages scan lifecycle transitions.

Design:
    - Entity (has identity via UUID)
    - Uses ScanStatus for lifecycle management
    - Uses ScanMode for execution strategy
"""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any
from domain.models.scan.value_objects.scan_status import ScanStatus

@dataclass
class SpatialScan:
    """Spatial scan entity."""
    
    # Identity
    id: UUID = field(default_factory=uuid4)
    
    # Type & Configuration
    scan_type: str = "manual"  # 'manual', 'serpentine', 'comb', etc.
    is_fly_scan: bool = False  # False = STEP_SCAN, True = FLY_SCAN
    
    # Lifecycle
    status: ScanStatus = ScanStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Results (simple dict for now, YAGNI)
    results: List[Dict[str, Any]] = field(default_factory=list)
    
    def start(self) -> None:
        """Start the scan."""
        if self.status != ScanStatus.PENDING:
            raise ValueError(f"Cannot start scan in status {self.status}")
        self.status = ScanStatus.RUNNING
        self.start_time = datetime.now()
    
    def complete(self) -> None:
        """Mark scan as completed."""
        if self.status != ScanStatus.RUNNING:
            raise ValueError(f"Cannot complete scan in status {self.status}")
        self.status = ScanStatus.COMPLETED
        self.end_time = datetime.now()
    
    def fail(self, reason: str) -> None:
        """Mark scan as failed."""
        if self.status not in (ScanStatus.RUNNING, ScanStatus.PAUSED):
            raise ValueError(f"Cannot fail scan in status {self.status}")
        self.status = ScanStatus.FAILED
        self.end_time = datetime.now()
    
    def cancel(self) -> None:
        """Cancel the scan."""
        if self.status.is_final():
            raise ValueError(f"Cannot cancel scan in final status {self.status}")
        self.status = ScanStatus.CANCELLED
        self.end_time = datetime.now()
    
    def pause(self) -> None:
        """Pause the scan."""
        if self.status != ScanStatus.RUNNING:
            raise ValueError(f"Cannot pause scan in status {self.status}")
        self.status = ScanStatus.PAUSED
    
    def resume(self) -> None:
        """Resume the scan after pause."""
        if self.status != ScanStatus.PAUSED:
            raise ValueError(f"Cannot resume scan in status {self.status}")
        self.status = ScanStatus.RUNNING
    
    def add_result(self, result: Dict[str, Any]) -> None:
        """Add a measurement result."""
        if self.status != ScanStatus.RUNNING:
            raise ValueError(f"Cannot add results when scan is {self.status}")
        self.results.append(result)
