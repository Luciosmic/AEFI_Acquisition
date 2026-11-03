import logging
from typing import Iterable

from application.services.scan_application_service.ports.i_unit_of_work import IUnitOfWork
from domain.scan.events.probe_acquisition_event.probe_acquisition_event import ProbeAcquisitionEvent
from domain.scan.events.scan_closure_failed.scan_closure_failed import ScanClosureFailed
from domain.scan.value_objects.scan_id.scan_id import ScanId
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)


class ScanClosureHandler:
    """Rattache chaque acquisition de sonde a son Scan dans une UoW separee (voir scan_closure_handler_intention.md)."""

    def __init__(self, event_bus: IDomainEventBus, uow: IUnitOfWork, acquisition_topics: Iterable[str]):
        self._event_bus = event_bus
        self._uow = uow
        for topic in acquisition_topics:
            event_bus.subscribe(topic, self.on_acquisition)

    def on_acquisition(self, event: ProbeAcquisitionEvent) -> None:
        scan_id, source, acquisition_id = event.scan_id, event.source, event.acquisition_id
        logger.info(
            "ScanClosureHandler: rattacher source=%s acquisition_id=%s au scan_id=%s", source, acquisition_id, scan_id
        )
        try:
            with self._uow:
                scan = self._uow.scans.get(ScanId(scan_id))
                if scan is None:
                    self._fail(scan_id, source, acquisition_id, "scan introuvable")
                    return
                if not scan.mark_acquired(source, acquisition_id):
                    logger.info(
                        "ScanClosureHandler: source=%s acquisition_id=%s deja recu par scan_id=%s, rien a faire",
                        source, acquisition_id, scan_id,
                    )
                    return
                self._uow.commit()
        except Exception as e:
            self._fail(scan_id, source, acquisition_id, f"{type(e).__name__}: {e}", exc_info=True)

    def _fail(self, scan_id, source, acquisition_id, reason: str, exc_info: bool = False) -> None:
        logger.error(
            "ScanClosureHandler: cloture impossible scan_id=%s source=%s acquisition_id=%s raison=%s",
            scan_id, source, acquisition_id, reason, exc_info=exc_info,
        )
        try:
            self._event_bus.publish(
                "scanclosurefailed",
                ScanClosureFailed(scan_id=scan_id, source=source, acquisition_id=acquisition_id, reason=reason),
            )
        except Exception:
            logger.exception("ScanClosureHandler: publication de ScanClosureFailed impossible scan_id=%s", scan_id)
