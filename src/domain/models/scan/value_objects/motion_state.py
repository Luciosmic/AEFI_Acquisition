"""
Motion State Value Object

Represents the execution state of an AtomicMotion.
"""

from enum import Enum, auto


class MotionState(Enum):
    """Execution state of an atomic motion."""
    
    PENDING = auto()      # Motion created but not yet started
    EXECUTING = auto()    # Motion is currently being executed
    COMPLETED = auto()    # Motion completed successfully
    FAILED = auto()       # Motion failed during execution

