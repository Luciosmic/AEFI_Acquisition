import logging
from typing import Dict, Optional

from application.services.scan_application_service.ports.i_unit_of_work import IUnitOfWork
from domain.scan.repositories.i_scan_repository import IScanRepository
from domain.scan.scan import Scan
from domain.scan.value_objects.scan_id.scan_id import ScanId

logger = logging.getLogger(__name__)


class InMemoryScanRepository(IScanRepository):
    """Repository mono-processus sans DB ; chaque agregat vu est enregistre aupres de l'UoW."""

    def __init__(self, uow: IUnitOfWork):
        self._uow = uow
        self._scans: Dict[ScanId, Scan] = {}

    def add(self, scan: Scan) -> None:
        logger.info("ScanRepository: add scan_id=%s state=%s", scan.id, scan.state.value)
        self._scans[scan.id] = scan
        self._uow.register(scan)

    def get(self, scan_id: ScanId) -> Optional[Scan]:
        scan = self._scans.get(scan_id)
        if scan is None:
            logger.info("ScanRepository: scan_id=%s inconnu", scan_id)
            return None
        self._uow.register(scan)
        return scan
