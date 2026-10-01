from enum import Enum, auto

class ExcitationMode(Enum):
    """Modes of excitation for the 4-sphere generator."""
    X_DIR = auto()
    Y_DIR = auto()
    CIRCULAR_PLUS = auto()
    CIRCULAR_MINUS = auto()
    CUSTOM = auto()
