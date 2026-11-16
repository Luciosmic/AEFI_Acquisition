"""
planned_scan_grid - The grid an acquisition planned for a scan (numpy only).
See planned_scan_grid_intention.md.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np

# Tolerance on a single-node axis, where no step gives a scale: relative to the coordinate.
_SINGLE_NODE_RELATIVE_TOLERANCE = 1e-9


@dataclass(frozen=True)
class PlannedAxis:
    """One axis of the planned grid: `points` evenly spaced nodes from `minimum` to `maximum`, both included."""

    minimum: float
    maximum: float
    points: int

    def __post_init__(self) -> None:
        if self.points < 1:
            raise ValueError(f"A planned axis needs at least one point, got {self.points}")
        if self.points > 1 and not self.maximum > self.minimum:
            raise ValueError(f"A planned axis of {self.points} points needs maximum > minimum, got [{self.minimum}, {self.maximum}]")

    @property
    def step(self) -> float:
        """Distance between two nodes; 1.0 for a single node, as the measured grid does."""
        return (self.maximum - self.minimum) / (self.points - 1) if self.points > 1 else 1.0

    def nodes(self) -> np.ndarray:
        return np.linspace(self.minimum, self.maximum, self.points)

    def node_indices(self, coordinates: np.ndarray) -> Optional[np.ndarray]:
        """Index of the nearest node of each coordinate, or None if one lies more than half a step from every node."""
        if self.points == 1:
            tolerance = _SINGLE_NODE_RELATIVE_TOLERANCE * max(1.0, abs(self.minimum))
            return np.zeros(len(coordinates), dtype=int) if np.all(np.abs(coordinates - self.minimum) <= tolerance) else None
        position = (coordinates - self.minimum) / self.step
        indices = np.rint(position).astype(int)
        # Half a step, widened by a rounding margin: a point exactly between two nodes still belongs to one.
        if np.any(indices < 0) or np.any(indices >= self.points) or np.any(np.abs(position - indices) > 0.5 + 1e-9):
            return None
        return indices


@dataclass(frozen=True)
class PlannedScanGrid:
    """The planned grid of a scan: its x axis (columns) and its y axis (rows)."""

    x: PlannedAxis
    y: PlannedAxis
