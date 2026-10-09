import logging
from typing import Any, List

from application.services.scan_application_service.ports.i_unit_of_work import IUnitOfWork
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)


class InMemoryUnitOfWork(IUnitOfWork):
    """UoW mono-processus sans DB : collecte les events des agregats vus, les publie apres commit."""

    def __init__(self, event_bus: IDomainEventBus):
        self._event_bus = event_bus
        self._seen: List[Any] = []
        self._committed = False

    def __enter__(self) -> "InMemoryUnitOfWork":
        self._seen = []
        self._committed = False
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if not self._committed:
            reason = f"exception {exc_type.__name__}" if exc_type else "commit non appele"
            logger.info("InMemoryUnitOfWork: rollback (%s), aucun evenement publie", reason)
        self._seen = []

    def register(self, aggregate: Any) -> None:
        if not any(a is aggregate for a in self._seen):
            self._seen.append(aggregate)

    def commit(self) -> None:
        events = [e for aggregate in self._seen for e in aggregate.domain_events]
        # Transaction fermee avant publication : un handler peut ouvrir une UoW (meme instance incluse).
        self._seen = []
        try:
            if not events:
                logger.info("InMemoryUnitOfWork: commit, rien a publier")
                return
            logger.info("InMemoryUnitOfWork: commit, publication de %d evenement(s)", len(events))
            for event in events:
                self._event_bus.publish(type(event).__name__.lower(), event)
        finally:
            self._committed = True
