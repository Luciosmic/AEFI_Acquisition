"""
MeasuredObject Registry — aggregate root of the measured_objects (see measured_object_registry_intention.md).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Sequence, Tuple
from uuid import uuid4

from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from domain.measured_object_registry.errors.measured_object_name_blank_error import MeasuredObjectNameBlankError
from domain.measured_object_registry.events.measured_object_registered.measured_object_registered import MeasuredObjectRegistered
from domain.shared_kernel.events.domain_event import DomainEvent


def _spelling(name: str) -> str:
    """The name as recorded: inner and outer spacing normalized."""
    return " ".join(name.split())


@dataclass
class MeasuredObjectRegistry:
    """Known measured_objects. Invariants: one spelling per measured_object (case and spacing
    insensitive), a non-blank name, stable identities."""

    measured_objects: List[MeasuredObject] = field(default_factory=list)
    _domain_events: List[DomainEvent] = field(default_factory=list, repr=False)

    @staticmethod
    def reconstitute(measured_objects: Sequence[MeasuredObject]) -> "MeasuredObjectRegistry":
        return MeasuredObjectRegistry(measured_objects=list(measured_objects))

    def register(self, name: str) -> Tuple[MeasuredObject, bool]:
        """The measured_object of this name, and whether it was just created."""
        spelling = _spelling(name)
        if not spelling:
            raise MeasuredObjectNameBlankError("un objet mesuré a un nom : saisie vide refusée")
        key = spelling.casefold()
        for known in self.measured_objects:
            if known.name.casefold() == key:
                return known, False
        measured_object = MeasuredObject(measured_object_id=uuid4(), name=spelling, registered_at=datetime.now(timezone.utc))
        self.measured_objects.append(measured_object)
        self._domain_events.append(
            MeasuredObjectRegistered(measured_object_id=measured_object.measured_object_id, name=measured_object.name, registered_at=measured_object.registered_at)
        )
        return measured_object, True

    @property
    def domain_events(self) -> List[DomainEvent]:
        """Events recorded since the last read — handed out once."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events
