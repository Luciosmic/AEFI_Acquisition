"""
Bench Referential

See bench_referential_intention.md.
"""

from dataclasses import dataclass, replace

LIMIT_SWITCH = "limit_switch"
CENTERED = "centered"
MODES = (LIMIT_SWITCH, CENTERED)


@dataclass(frozen=True)
class BenchReferential:
    mode: str = LIMIT_SWITCH
    max_x_mm: float = 1270.0
    max_y_mm: float = 1270.0

    @property
    def is_centered(self) -> bool:
        return self.mode == CENTERED

    def with_mode(self, mode: str) -> "BenchReferential":
        return replace(self, mode=mode if mode in MODES else LIMIT_SWITCH)

    def with_limits(self, max_x_mm: float, max_y_mm: float) -> "BenchReferential":
        return replace(self, max_x_mm=max_x_mm, max_y_mm=max_y_mm)

    def to_raw_x(self, displayed: float) -> float:
        return displayed + self.max_x_mm / 2.0 if self.is_centered else displayed

    def to_raw_y(self, displayed: float) -> float:
        return displayed + self.max_y_mm / 2.0 if self.is_centered else displayed

    def to_display_x(self, raw: float) -> float:
        return raw - self.max_x_mm / 2.0 if self.is_centered else raw

    def to_display_y(self, raw: float) -> float:
        return raw - self.max_y_mm / 2.0 if self.is_centered else raw
