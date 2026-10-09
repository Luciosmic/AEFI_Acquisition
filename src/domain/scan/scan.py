"""Scan aggregate root (see scan_intention.md)."""

from dataclasses import dataclass, field
from typing import List, Set

from domain.aefi_point.value_objects.aefi_point_id.aefi_point_id import AefiPointId
from domain.scan.errors.scan_already_completed_error import ScanAlreadyCompletedError
from domain.scan.errors.scan_already_started_error import ScanAlreadyStartedError
from domain.scan.errors.scan_not_started_error import ScanNotStartedError
from domain.scan.value_objects.scan_id.scan_id import ScanId
from domain.scan.value_objects.scan_state.scan_state import ScanState
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted


@dataclass
class Scan:
    id: ScanId
    expected_points: int
    _state: ScanState = ScanState.PENDING
    _received: Set[AefiPointId] = field(default_factory=set)
    _domain_events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        if self.expected_points < 1:
            raise ValueError("expected_points must be >= 1")

    @property
    def state(self) -> ScanState:
        return self._state

    @property
    def received_point_ids(self) -> frozenset:
        return frozenset(self._received)

    @property
    def domain_events(self) -> List[DomainEvent]:
        """Get and clear domain events."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def start(self) -> None:
        if self._state is not ScanState.PENDING:
            raise ScanAlreadyStartedError(self.id, self._state)
        self._state = ScanState.STARTED

    def mark_point_acquired(self, aefi_point_id: AefiPointId) -> bool:
        """Retourne True si le point est nouveau, False s'il était déjà reçu (no-op)."""
        if aefi_point_id in self._received:
            return False
        if self._state is ScanState.PENDING:
            raise ScanNotStartedError(self.id, aefi_point_id)
        if self._state is ScanState.COMPLETED:
            raise ScanAlreadyCompletedError(self.id, aefi_point_id)
        self._received.add(aefi_point_id)
        if len(self._received) == self.expected_points:
            self._state = ScanState.COMPLETED
            self._domain_events.append(ScanCompleted(scan_id=self.id, total_points=self.expected_points))
        return True
