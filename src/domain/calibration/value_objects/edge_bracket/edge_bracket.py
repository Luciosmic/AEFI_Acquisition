"""
Edge Bracket Value Object

See edge_bracket_intention.md.
"""

from dataclasses import dataclass, replace
from typing import Optional

from domain.calibration.value_objects.bar_point_reading.bar_point_reading import BarPointClassification


@dataclass(frozen=True)
class EdgeBracket:
    """Oriented bracket [a, b] of one bar front, in motor increments:
    `on_bar_increment` (a) was classified on the bar, `off_bar_increment` (b) off it."""

    on_bar_increment: int
    off_bar_increment: int
    # True once a probe inside the bracket could not be classified (LIDAR noise limit).
    stopped_undecidable: bool = False

    def __post_init__(self):
        if self.on_bar_increment == self.off_bar_increment:
            raise ValueError(
                f"a bracket needs distinct sides, got on_bar=off_bar={self.on_bar_increment}"
            )

    @staticmethod
    def around(front_increment: float, on_bar_direction: int, margin_increments: int) -> "EdgeBracket":
        """Coarse bracket around a front located by the fly scan: `on_bar_direction`
        is +1 when the bar lies on the greater increments, -1 otherwise."""
        if on_bar_direction not in (1, -1):
            raise ValueError(f"on_bar_direction must be +1 or -1, got {on_bar_direction}")
        if margin_increments < 1:
            raise ValueError(f"margin_increments must be >= 1, got {margin_increments}")
        center = round(front_increment)
        return EdgeBracket(
            on_bar_increment=center + on_bar_direction * margin_increments,
            off_bar_increment=center - on_bar_direction * margin_increments,
        )

    @property
    def width_increments(self) -> int:
        return abs(self.off_bar_increment - self.on_bar_increment)

    @property
    def on_bar_direction(self) -> int:
        """+1 when the bar side is on the greater increments."""
        return 1 if self.on_bar_increment > self.off_bar_increment else -1

    @property
    def is_at_motor_resolution(self) -> bool:
        return self.width_increments <= 1

    @property
    def is_resolved(self) -> bool:
        """Refinement over: one increment wide, or a probe was undecidable."""
        return self.is_at_motor_resolution or self.stopped_undecidable

    @property
    def center_increment(self) -> float:
        """n = (a + b) / 2."""
        return (self.on_bar_increment + self.off_bar_increment) / 2.0

    @property
    def half_width_increments(self) -> float:
        """δ = |b − a| / 2."""
        return self.width_increments / 2.0

    def next_probe(self) -> Optional[int]:
        """Integer midpoint strictly between a and b; None once resolved."""
        if self.is_resolved:
            return None
        return self.on_bar_increment + (self.off_bar_increment - self.on_bar_increment) // 2

    def narrowed(self, probe_increment: int, classification: BarPointClassification) -> "EdgeBracket":
        """Bracket after classifying `probe_increment` (dichotomy). An undecidable
        probe stops the refinement and leaves [a, b] unchanged."""
        low, high = sorted((self.on_bar_increment, self.off_bar_increment))
        if not low < probe_increment < high:
            raise ValueError(f"probe {probe_increment} is not strictly inside [{low}, {high}]")
        if classification is BarPointClassification.ON_BAR:
            return replace(self, on_bar_increment=probe_increment)
        if classification is BarPointClassification.OFF_BAR:
            return replace(self, off_bar_increment=probe_increment)
        return replace(self, stopped_undecidable=True)

    def widened(self, margin_increments: int) -> "EdgeBracket":
        """Each side pushed `margin_increments` further from the other (a coarse
        bracket whose sides did not check out at rest)."""
        if margin_increments < 1:
            raise ValueError(f"margin_increments must be >= 1, got {margin_increments}")
        direction = self.on_bar_direction
        return EdgeBracket(
            on_bar_increment=self.on_bar_increment + direction * margin_increments,
            off_bar_increment=self.off_bar_increment - direction * margin_increments,
        )

    def with_sides(self, on_bar_increment: int, off_bar_increment: int) -> "EdgeBracket":
        """Same refinement state, sides moved (e.g. clamped to the travel)."""
        return replace(self, on_bar_increment=on_bar_increment, off_bar_increment=off_bar_increment)
