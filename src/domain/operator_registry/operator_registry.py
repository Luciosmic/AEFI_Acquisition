"""
Operator Registry — aggregate root of the operators (see operator_registry_intention.md).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Sequence, Tuple
from uuid import uuid4

from domain.operator_registry.entities.operator.operator import Operator
from domain.operator_registry.errors.operator_name_blank_error import OperatorNameBlankError
from domain.operator_registry.events.operator_registered.operator_registered import OperatorRegistered
from domain.shared_kernel.events.domain_event import DomainEvent


def _spelling(name: str) -> str:
    """The name as recorded: inner and outer spacing normalized."""
    return " ".join(name.split())


@dataclass
class OperatorRegistry:
    """Known operators. Invariants: one spelling per operator (case and spacing
    insensitive), a non-blank name, stable identities."""

    operators: List[Operator] = field(default_factory=list)
    _domain_events: List[DomainEvent] = field(default_factory=list, repr=False)

    @staticmethod
    def reconstitute(operators: Sequence[Operator]) -> "OperatorRegistry":
        return OperatorRegistry(operators=list(operators))

    def register(self, name: str) -> Tuple[Operator, bool]:
        """The operator of this name, and whether it was just created."""
        spelling = _spelling(name)
        if not spelling:
            raise OperatorNameBlankError("un opérateur a un nom : saisie vide refusée")
        key = spelling.casefold()
        for known in self.operators:
            if known.name.casefold() == key:
                return known, False
        operator = Operator(operator_id=uuid4(), name=spelling, registered_at=datetime.now(timezone.utc))
        self.operators.append(operator)
        self._domain_events.append(
            OperatorRegistered(operator_id=operator.operator_id, name=operator.name, registered_at=operator.registered_at)
        )
        return operator, True

    @property
    def domain_events(self) -> List[DomainEvent]:
        """Events recorded since the last read — handed out once."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events
