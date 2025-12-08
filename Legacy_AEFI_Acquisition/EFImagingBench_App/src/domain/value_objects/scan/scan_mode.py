"""
Domain: Scan Mode

Responsibility:
    Enumeration of scan trajectory patterns.

Rationale:
    Defines how the scan moves through the scan zone.
    Different modes optimize for different objectives (speed, coverage, etc.).

Design:
    - Standard Python Enum
    - Clear naming matching domain terminology
"""
from enum import Enum, auto

class ScanMode(Enum):
    """Scan trajectory patterns.
    
    Defines the path taken through the scan zone:
    - SERPENTINE: Zigzag pattern (efficient, continuous)
    - RASTER: Line-by-line, always same direction (simple)
    - COMB: Scan each line independently (good for testing)
    """
    
    SERPENTINE = auto()  # Zigzag: →→→ ←←← →→→
    RASTER = auto()      # Always same direction: →→→ →→→ →→→
    COMB = auto()        # Independent lines: →→→ (return) →→→

