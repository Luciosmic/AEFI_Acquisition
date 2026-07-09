from enum import Enum, auto

class ScanAxis(Enum):
    """Fast axis for RASTER and SERPENTINE scan patterns.

    Y: scan along Y columns first (outer=X, inner=Y) — preferred default.
    X: scan along X rows first (outer=Y, inner=X) — legacy behavior.
    """
    Y = auto()
    X = auto()
