"""Scan aggregate root (see scan_intention.md)."""

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Set
from uuid import UUID

from domain.scan.errors.scan_already_completed_error import ScanAlreadyCompletedError
from domain.scan.errors.scan_already_started_error import ScanAlreadyStartedError
from domain.scan.errors.scan_not_started_error import ScanNotStartedError
from domain.scan.errors.scan_source_not_declared_error import ScanSourceNotDeclaredError
from domain.scan.value_objects.expected_source.expected_source import ExpectedSource
from domain.scan.value_objects.scan_id.scan_id import ScanId
from domain.scan.value_objects.scan_state.scan_state import ScanState
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted


@dataclass
class Scan:
    id: ScanId
    expected_sources: Mapping[str, ExpectedSource]
    total_points: int
    _state: ScanState = ScanState.PENDING
    _received: Dict[str, Set[UUID]] = field(default_factory=dict)
    _domain_events: List[DomainEvent] = field(default_factory=list)

    def __post_init__(self):
        if self.total_points < 1:
            raise ValueError("total_points must be >= 1")
        if not any(source.required for source in self.expected_sources.values()):
            raise ValueError("at least one required source must be declared")
        self._received = {name: set() for name in self.expected_sources}

    @property
    def state(self) -> ScanState:
        return self._state

    def received(self, source: str) -> frozenset:
        return frozenset(self._received[source])

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

    def mark_acquired(self, source: str, acquisition_id: UUID) -> bool:
        """Retourne True si l'acquisition est nouvelle, False si elle était déjà reçue (no-op)."""
        if source not in self.expected_sources:
            raise ScanSourceNotDeclaredError(self.id, source, acquisition_id)
        if acquisition_id in self._received[source]:
            return False
        if self._state is ScanState.PENDING:
            raise ScanNotStartedError(self.id, acquisition_id)
        if self._state is ScanState.COMPLETED:
            raise ScanAlreadyCompletedError(self.id, acquisition_id)
        self._received[source].add(acquisition_id)
        if self._all_required_sources_complete():
            self._state = ScanState.COMPLETED
            self._domain_events.append(ScanCompleted(scan_id=self.id, total_points=self.total_points))
        return True

    def _all_required_sources_complete(self) -> bool:
        return all(
            len(self._received[name]) >= expected.count
            for name, expected in self.expected_sources.items()
            if expected.required
        )
