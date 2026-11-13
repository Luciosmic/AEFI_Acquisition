import logging
import threading
from typing import Any, List, Optional, Tuple

from application.scan.scan_application_service.ports.i_unit_of_work import IUnitOfWork
from domain.shared_kernel.events.i_domain_event_bus.i_domain_event_bus import IDomainEventBus
from infrastructure.persistence.aefi_line.in_memory_aefi_line_repository import InMemoryAefiLineRepository
from infrastructure.persistence.aefi_point.in_memory_aefi_point_repository import InMemoryAefiPointRepository
from infrastructure.persistence.narda_point.in_memory_narda_point_repository import InMemoryNardaPointRepository
from infrastructure.persistence.scan.in_memory_scan_repository import InMemoryScanRepository

logger = logging.getLogger(__name__)

# File de dispatch du thread courant, partagee par toutes les instances : un handler peut committer
# via une autre instance que celle qui livre. None = aucun dispatch en cours sur ce thread.
# Elle vit ici et non dans le bus : le bus est appele depuis des threads materiels, sa semantique
# (livraison immediate) reste inchangee pour les publications directes.
_dispatch = threading.local()


class _Transaction(threading.local):
    """Transaction en cours d'UN thread sur UNE instance : __init__ est rejoue a la premiere lecture par thread."""

    def __init__(self) -> None:
        self.seen: List[Any] = []
        self.committed = False


class InMemoryUnitOfWork(IUnitOfWork):
    """UoW mono-processus sans DB : collecte les events des agregats vus, les publie apres commit.

    La transaction en cours (agregats vus, commit fait) est propre a chaque thread : une meme instance
    est partagee par tous les threads (main.py), et un `with uow:` du thread UI ne doit pas vider celle
    que la boucle de scan a ouverte. Le stockage (repositories) reste partage : un agregat commite par
    un thread est lisible par un autre.

    Le commit le plus externe d'un thread possede une file FIFO et la vide : chaque evenement est livre
    a tous ses abonnes ("*" compris) avant le suivant. Un commit imbrique (fait par un handler pendant
    la livraison) ajoute ses evenements en fin de file et retourne : un evenement produit en reaction
    ne peut pas etre observe avant celui qui l'a cause (ex. ScanCompleted apres la derniere AefiLineAcquired).
    """

    def __init__(self, event_bus: IDomainEventBus):
        self._event_bus = event_bus
        self._tx = _Transaction()
        self.aefi_points = InMemoryAefiPointRepository(self)
        self.aefi_lines = InMemoryAefiLineRepository(self)
        self.narda_points = InMemoryNardaPointRepository(self)
        self.scans = InMemoryScanRepository(self)

    def __enter__(self) -> "InMemoryUnitOfWork":
        self._tx.seen = []
        self._tx.committed = False
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if not self._tx.committed:
            reason = f"exception {exc_type.__name__}" if exc_type else "commit non appele"
            logger.info("InMemoryUnitOfWork: rollback (%s), aucun evenement publie", reason)
        self._tx.seen = []

    def register(self, aggregate: Any) -> None:
        seen = self._tx.seen
        if not any(a is aggregate for a in seen):
            seen.append(aggregate)

    def commit(self) -> None:
        events = [e for aggregate in self._tx.seen for e in aggregate.domain_events]
        # Transaction fermee avant publication : un handler peut ouvrir une UoW (meme instance incluse).
        self._tx.seen = []
        try:
            if not events:
                logger.info("InMemoryUnitOfWork: commit, rien a publier")
                return
            queue: Optional[List[Tuple[IDomainEventBus, Any]]] = getattr(_dispatch, "queue", None)
            if queue is not None:
                logger.info(
                    "InMemoryUnitOfWork: commit imbrique pendant une livraison, %d evenement(s) mis en fin de file "
                    "(%d deja en attente), livres apres l'evenement en cours",
                    len(events), len(queue),
                )
                queue.extend((self._event_bus, e) for e in events)
                return
            logger.info("InMemoryUnitOfWork: commit, publication de %d evenement(s)", len(events))
            self._dispatch_queue([(self._event_bus, e) for e in events])
        finally:
            self._tx.committed = True

    @staticmethod
    def _dispatch_queue(queue: List[Tuple[IDomainEventBus, Any]]) -> None:
        """Vide la file en FIFO ; les commits imbriques des handlers l'allongent pendant la boucle."""
        _dispatch.queue = queue
        try:
            while queue:
                bus, event = queue.pop(0)
                bus.publish(type(event).__name__.lower(), event)
        except Exception as e:
            logger.error(
                "InMemoryUnitOfWork: livraison interrompue (%s), %d evenement(s) en file non livres",
                type(e).__name__, len(queue),
            )
            raise
        finally:
            # Remis a zero meme sur exception : sinon tout commit suivant du thread s'empilerait dans une file morte.
            _dispatch.queue = None
