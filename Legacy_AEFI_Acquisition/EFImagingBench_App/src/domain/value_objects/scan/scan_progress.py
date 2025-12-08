"""
Domain: Scan Progress

Responsibility:
    Represents the current progress of a running scan.

Rationale:
    Provides real-time progress information for monitoring and UI updates.
    Immutable snapshot of progress at a given moment.

Design:
    - Frozen dataclass (immutable)
    - Provides derived calculations (percentage, ETA)
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class ScanProgress:
    """Progress information for a running scan.
    
    Immutable snapshot of scan progress at a given moment.
    """
    
    # Point progress
    current_point: int  # 0-indexed
    total_points: int
    
    # Line progress
    current_line: int  # 0-indexed
    total_lines: int
    
    # Time progress
    elapsed_time_seconds: float
    estimated_remaining_seconds: float
    
    def __post_init__(self):
        """Validate progress values."""
        if self.current_point < 0 or self.current_point > self.total_points:
            raise ValueError(f"Invalid current_point: {self.current_point}/{self.total_points}")
        
        if self.current_line < 0 or self.current_line > self.total_lines:
            raise ValueError(f"Invalid current_line: {self.current_line}/{self.total_lines}")
        
        if self.elapsed_time_seconds < 0:
            raise ValueError(f"elapsed_time_seconds must be >= 0, got {self.elapsed_time_seconds}")
        
        if self.estimated_remaining_seconds < 0:
            raise ValueError(f"estimated_remaining_seconds must be >= 0, got {self.estimated_remaining_seconds}")
    
    def percentage(self) -> float:
        """Calculate completion percentage (0-100)."""
        if self.total_points == 0:
            return 0.0
        return (self.current_point / self.total_points) * 100.0
    
    def is_complete(self) -> bool:
        """Check if scan is complete."""
        return self.current_point >= self.total_points

