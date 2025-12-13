"""
Domain: Scan

Responsibility:
    Enumeration of available scan types.

Rationale:
    Provides a type-safe way to distinguish between different scanning strategies (Manual, Serpentine, etc.).
    Used for dispatching logic and metadata tagging.

Design:
    - Standard Python Enum
"""
from enum import Enum, auto

class ScanType(Enum):
    MANUAL = auto()
    SERPENTINE = auto()
    COMB = auto()
    CUSTOM = auto()
    STABILITY = auto()
    TEMPORAL = auto()
    FREQUENCY = auto()
