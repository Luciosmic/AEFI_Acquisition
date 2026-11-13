"""
MeasuredObject Registry — aggregate root of the measured_objects (see measured_object_registry_intention.md).
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import List, Sequence, Tuple
from uuid import UUID, uuid4

from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from domain.measured_object_registry.errors.measured_object_name_blank_error import MeasuredObjectNameBlankError
from domain.measured_object_registry.errors.measured_object_name_taken_error import MeasuredObjectNameTakenError
from domain.measured_object_registry.errors.measured_object_not_found_error import MeasuredObjectNotFoundError
from domain.measured_object_registry.events.measured_object_deleted.measured_object_deleted import MeasuredObjectDeleted
from domain.measured_object_registry.events.measured_object_registered.measured_object_registered import MeasuredObjectRegistered
from domain.measured_object_registry.events.measured_object_renamed.measured_object_renamed import MeasuredObjectRenamed
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


def _spelling(name: str) -> str:
    """The name as recorded: inner and outer spacing normalized."""
    return " ".join(name.split())


def _required_spelling(name: str) -> str:
    spelling = _spelling(name)
    if not spelling:
        raise MeasuredObjectNameBlankError("un objet mesuré a un nom : saisie vide refusée")
    return spelling


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
        spelling = _required_spelling(name)
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

    def rename(self, measured_object_id: UUID, name: str) -> Tuple[MeasuredObject, bool]:
        """The measured_object under its new name, and whether the recorded name changed.
        Same identity: the acquisitions already made keep pointing at it."""
        index = self._index_of(measured_object_id)
        current = self.measured_objects[index]
        spelling = _required_spelling(name)
        if spelling == current.name:
            return current, False
        key = spelling.casefold()
        for other in self.measured_objects:
            if other.measured_object_id != measured_object_id and other.name.casefold() == key:
                raise MeasuredObjectNameTakenError(f"un autre objet mesuré s'appelle déjà « {other.name} »")
        renamed = replace(current, name=spelling)
        self.measured_objects[index] = renamed
        self._domain_events.append(MeasuredObjectRenamed(
            measured_object_id=measured_object_id, previous_name=current.name, name=spelling,
            renamed_at=datetime.now(timezone.utc),
        ))
        return renamed, True

    def delete(self, measured_object_id: UUID) -> MeasuredObject:
        """Remove the measured_object from the registry; returns what was removed.
        Its identity is never given to another measured_object (I3)."""
        removed = self.measured_objects.pop(self._index_of(measured_object_id))
        self._domain_events.append(MeasuredObjectDeleted(
            measured_object_id=removed.measured_object_id, name=removed.name, deleted_at=datetime.now(timezone.utc),
        ))
        return removed

    def _index_of(self, measured_object_id: UUID) -> int:
        for index, known in enumerate(self.measured_objects):
            if known.measured_object_id == measured_object_id:
                return index
        raise MeasuredObjectNotFoundError(f"aucun objet mesuré d'identité {measured_object_id} dans le registre")

    @property
    def domain_events(self) -> List[DomainEvent]:
        """Events recorded since the last read — handed out once."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events
