"""
Edge Bracket Value Object

See edge_bracket_intention.md.
"""

from dataclasses import dataclass, replace
from typing import Optional

from domain.calibration.value_objects.bar_point_reading.bar_point_reading import BarPointClassification


def _midpoint(x: int, y: int) -> int:
    """Integer point strictly between x and y when |y − x| ≥ 2."""
    return x + (y - x) // 2


def _strictly_between(p: int, x: int, y: int) -> bool:
    return min(x, y) < p < max(x, y)


@dataclass(frozen=True)
class EdgeBracket:
    """Oriented bracket [a, b] of one bar front, in motor increments:
    `on_bar_increment` (a) was classified on the bar, `off_bar_increment` (b) off it.

    Once a probe is undecidable, the LIDAR noise zone lies inside [a, b]:
    `undecidable_near_on` / `undecidable_near_off` are the undecidable points
    closest to a and to b, and each side is refined on its own toward the zone."""

    on_bar_increment: int
    off_bar_increment: int
    undecidable_near_on: Optional[int] = None
    undecidable_near_off: Optional[int] = None

    def __post_init__(self):
        if self.on_bar_increment == self.off_bar_increment:
            raise ValueError(
                f"a bracket needs distinct sides, got on_bar=off_bar={self.on_bar_increment}"
            )
        if (self.undecidable_near_on is None) != (self.undecidable_near_off is None):
            raise ValueError("the undecidable zone needs both its ends")
        if self.undecidable_near_on is not None:
            for point in (self.undecidable_near_on, self.undecidable_near_off):
                if not _strictly_between(point, self.on_bar_increment, self.off_bar_increment):
                    raise ValueError(f"undecidable point {point} outside the bracket")

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
    def limited_by_lidar_noise(self) -> bool:
        """An undecidable zone sits inside the bracket: the LIDAR noise, not the
        motor, bounds the resolution."""
        return self.undecidable_near_on is not None

    @property
    def _on_side_done(self) -> bool:
        return abs(self.undecidable_near_on - self.on_bar_increment) <= 1

    @property
    def _off_side_done(self) -> bool:
        return abs(self.off_bar_increment - self.undecidable_near_off) <= 1

    @property
    def is_resolved(self) -> bool:
        """Refinement over: one increment wide, or each side one increment from
        the undecidable zone."""
        if self.is_at_motor_resolution:
            return True
        return self.limited_by_lidar_noise and self._on_side_done and self._off_side_done

    @property
    def center_increment(self) -> float:
        """n = (a + b) / 2."""
        return (self.on_bar_increment + self.off_bar_increment) / 2.0

    @property
    def half_width_increments(self) -> float:
        """δ = |b − a| / 2."""
        return self.width_increments / 2.0

    def next_probe(self) -> Optional[int]:
        """Dichotomy: midpoint of [a, b]; once an undecidable zone is known, the
        midpoint between a and the zone, then between the zone and b. None once resolved."""
        if self.is_resolved:
            return None
        if not self.limited_by_lidar_noise:
            return _midpoint(self.on_bar_increment, self.off_bar_increment)
        if not self._on_side_done:
            return _midpoint(self.on_bar_increment, self.undecidable_near_on)
        return _midpoint(self.undecidable_near_off, self.off_bar_increment)

    def narrowed(self, probe_increment: int, classification: BarPointClassification) -> "EdgeBracket":
        """Bracket after classifying `probe_increment`. An undecidable probe does
        not stop the refinement: it becomes an end of the undecidable zone."""
        p = probe_increment
        a, b = self.on_bar_increment, self.off_bar_increment
        if not _strictly_between(p, a, b):
            raise ValueError(f"probe {p} is not strictly inside [{min(a, b)}, {max(a, b)}]")
        if not self.limited_by_lidar_noise:
            if classification is BarPointClassification.ON_BAR:
                return replace(self, on_bar_increment=p)
            if classification is BarPointClassification.OFF_BAR:
                return replace(self, off_bar_increment=p)
            return replace(self, undecidable_near_on=p, undecidable_near_off=p)

        on_side = not _strictly_between(p, self.undecidable_near_on, b)  # between a and the zone
        if classification is BarPointClassification.UNDECIDABLE:
            if on_side:
                return replace(self, undecidable_near_on=p)
            return replace(self, undecidable_near_off=p)
        if classification is BarPointClassification.ON_BAR:
            if _strictly_between(p, a, self.undecidable_near_on):
                return replace(self, on_bar_increment=p)
            # On the bar beyond the zone (noise): the zone is behind the new a.
            return EdgeBracket(on_bar_increment=p, off_bar_increment=b)
        if _strictly_between(p, self.undecidable_near_off, b):
            return replace(self, off_bar_increment=p)
        # Off the bar before the zone (noise): the zone is behind the new b.
        return EdgeBracket(on_bar_increment=a, off_bar_increment=p)

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
        """Same bracket with its sides moved (e.g. clamped to the travel), before refinement."""
        return EdgeBracket(on_bar_increment=on_bar_increment, off_bar_increment=off_bar_increment)
