"""AefiLine aggregate root (see aefi_line_intention.md)."""

from dataclasses import dataclass, field
from typing import List, Sequence, Tuple
from uuid import UUID

from domain.aefi_line.errors.aefi_line_already_acquired_error import AefiLineAlreadyAcquiredError
from domain.aefi_line.errors.aefi_line_incomplete_error import AefiLineIncompleteError
from domain.aefi_line.events.aefi_line_acquired.aefi_line_acquired import AefiLineAcquired
from domain.aefi_line.value_objects.aefi_line_id.aefi_line_id import AefiLineId
from domain.aefi_line.value_objects.line_grid_point.line_grid_point import LineGridPoint
from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass
class AefiLine:
    id: AefiLineId
    scan_id: UUID
    line_index: int
    expected_points: int
    _points: Tuple[LineGridPoint, ...] = ()
    _domain_events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        if self.expected_points < 1:
            raise ValueError("expected_points must be >= 1")

    @property
    def points(self) -> Tuple[LineGridPoint, ...]:
        return self._points

    @property
    def is_acquired(self) -> bool:
        return bool(self._points)

    @property
    def domain_events(self) -> List[DomainEvent]:
        """Get and clear domain events."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def record_points(self, points: Sequence[LineGridPoint]) -> None:
        if self.is_acquired:
            raise AefiLineAlreadyAcquiredError(self.id)
        indices = [p.index_in_line for p in points]
        expected = set(range(self.expected_points))
        if len(indices) != self.expected_points or set(indices) != expected:
            raise AefiLineIncompleteError(self.id, self.expected_points, sorted(expected - set(indices)), len(indices))
        self._points = tuple(sorted(points, key=lambda p: p.index_in_line))
        self._domain_events.append(
            AefiLineAcquired(
                aefi_line_id=self.id,
                scan_id=self.scan_id,
                line_index=self.line_index,
                points=self._points,
                points_count=len(self._points),
            )
        )
