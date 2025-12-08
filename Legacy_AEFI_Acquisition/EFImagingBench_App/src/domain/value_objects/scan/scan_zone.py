"""
Domain: Scan Zone

Responsibility:
    Defines a rectangular 2D scanning zone with physical limits validation.

Rationale:
    Encapsulates the spatial boundaries of a scan area.
    Validates against physical bench limits to prevent invalid movements.

Design:
    - Frozen dataclass (immutable)
    - Validates physical limits in __post_init__
    - TODO: Inject limits from TestBench entity instead of hardcoding
"""
from dataclasses import dataclass
from ..geometric.position_2d import Position2D

# Physical limits of the test bench (hardcoded for MVP)
# TODO: Inject from TestBench entity
PHYSICAL_X_MAX_CM = 120.0
PHYSICAL_Y_MAX_CM = 120.0

@dataclass(frozen=True)
class ScanZone:
    """Rectangular 2D scanning zone.
    
    Defines the spatial boundaries for a scan operation.
    Validates against physical bench limits.
    """
    
    x_min: float  # cm
    x_max: float  # cm
    y_min: float  # cm
    y_max: float  # cm
    
    def __post_init__(self):
        """Validate zone boundaries."""
        # Validate X range
        if not (0 <= self.x_min < self.x_max <= PHYSICAL_X_MAX_CM):
            raise ValueError(
                f"Invalid X range: [{self.x_min}, {self.x_max}]. "
                f"Must be 0 <= x_min < x_max <= {PHYSICAL_X_MAX_CM}"
            )
        
        # Validate Y range
        if not (0 <= self.y_min < self.y_max <= PHYSICAL_Y_MAX_CM):
            raise ValueError(
                f"Invalid Y range: [{self.y_min}, {self.y_max}]. "
                f"Must be 0 <= y_min < y_max <= {PHYSICAL_Y_MAX_CM}"
            )
    
    def contains(self, position: Position2D) -> bool:
        """Check if a position is within this zone."""
        return (self.x_min <= position.x <= self.x_max and
                self.y_min <= position.y <= self.y_max)
    
    def area(self) -> float:
        """Calculate the area of the zone in cm²."""
        return (self.x_max - self.x_min) * (self.y_max - self.y_min)
    
    def center(self) -> Position2D:
        """Calculate the center position of the zone."""
        return Position2D(
            x=(self.x_min + self.x_max) / 2,
            y=(self.y_min + self.y_max) / 2
        )

