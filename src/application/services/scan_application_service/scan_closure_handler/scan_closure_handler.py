import logging

from application.services.scan_application_service.ports.i_unit_of_work import IUnitOfWork
from domain.aefi_point.events.aefi_point_acquired.aefi_point_acquired import AefiPointAcquired
from domain.scan.events.scan_closure_failed.scan_closure_failed import ScanClosureFailed
from domain.scan.value_objects.scan_id.scan_id import ScanId
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)


class ScanClosureHandler:
    """Rattache chaque AefiPointAcquired a son Scan dans une UoW separee (voir scan_closure_handler_intention.md)."""

    def __init__(self, event_bus: IDomainEventBus, uow: IUnitOfWork):
        self._event_bus = event_bus
        self._uow = uow
        event_bus.subscribe("aefipointacquired", self.on_aefi_point_acquired)

    def on_aefi_point_acquired(self, event: AefiPointAcquired) -> None:
        scan_id, point_id = event.scan_id, event.aefi_point_id
        logger.info("ScanClosureHandler: rattacher aefi_point_id=%s au scan_id=%s", point_id, scan_id)
        try:
            with self._uow:
                scan = self._uow.scans.get(ScanId(scan_id))
                if scan is None:
                    self._fail(scan_id, point_id, "scan introuvable")
                    return
                if not scan.mark_point_acquired(point_id):
                    logger.info(
                        "ScanClosureHandler: aefi_point_id=%s deja recu par scan_id=%s, rien a faire", point_id, scan_id
                    )
                    return
                self._uow.commit()
        except Exception as e:
            self._fail(scan_id, point_id, f"{type(e).__name__}: {e}", exc_info=True)

    def _fail(self, scan_id, point_id, reason: str, exc_info: bool = False) -> None:
        logger.error(
            "ScanClosureHandler: cloture impossible scan_id=%s aefi_point_id=%s raison=%s",
            scan_id, point_id, reason, exc_info=exc_info,
        )
        try:
            self._event_bus.publish(
                "scanclosurefailed", ScanClosureFailed(scan_id=scan_id, aefi_point_id=point_id, reason=reason)
            )
        except Exception:
            logger.exception("ScanClosureHandler: publication de ScanClosureFailed impossible scan_id=%s", scan_id)
