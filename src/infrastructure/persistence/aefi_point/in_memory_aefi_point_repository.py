import logging
from typing import Dict, List, Optional
from uuid import UUID

from application.services.scan_application_service.ports.i_unit_of_work import IUnitOfWork
from domain.aefi_point.aefi_point import AefiPoint
from domain.aefi_point.repositories.i_aefi_point_repository import IAefiPointRepository
from domain.aefi_point.value_objects.aefi_point_id.aefi_point_id import AefiPointId

logger = logging.getLogger(__name__)


class InMemoryAefiPointRepository(IAefiPointRepository):
    """Repository mono-processus sans DB ; chaque agregat vu est enregistre aupres de l'UoW."""

    def __init__(self, uow: IUnitOfWork):
        self._uow = uow
        self._points: Dict[AefiPointId, AefiPoint] = {}

    def add(self, point: AefiPoint) -> None:
        logger.info("AefiPointRepository: add aefi_point_id=%s scan_id=%s", point.id, point.scan_id)
        self._points[point.id] = point
        self._uow.register(point)

    def get(self, point_id: AefiPointId) -> Optional[AefiPoint]:
        point = self._points.get(point_id)
        if point is None:
            logger.info("AefiPointRepository: aefi_point_id=%s inconnu", point_id)
            return None
        self._uow.register(point)
        return point

    def list_by_scan(self, scan_id: UUID) -> List[AefiPoint]:
        points = [p for p in self._points.values() if p.scan_id == scan_id]
        for p in points:
            self._uow.register(p)
        return points
