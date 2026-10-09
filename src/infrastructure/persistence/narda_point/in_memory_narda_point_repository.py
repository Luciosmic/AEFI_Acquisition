import logging
from typing import Dict, List, Optional
from uuid import UUID

from application.services.scan_application_service.ports.i_unit_of_work import IUnitOfWork
from domain.narda_point.narda_point import NardaPoint
from domain.narda_point.repositories.i_narda_point_repository import INardaPointRepository
from domain.narda_point.value_objects.narda_point_id.narda_point_id import NardaPointId

logger = logging.getLogger(__name__)


class InMemoryNardaPointRepository(INardaPointRepository):
    """Repository mono-processus sans DB ; chaque agregat vu est enregistre aupres de l'UoW."""

    def __init__(self, uow: IUnitOfWork):
        self._uow = uow
        self._points: Dict[NardaPointId, NardaPoint] = {}

    def add(self, point: NardaPoint) -> None:
        logger.info("NardaPointRepository: add narda_point_id=%s scan_id=%s", point.id, point.scan_id)
        self._points[point.id] = point
        self._uow.register(point)

    def get(self, point_id: NardaPointId) -> Optional[NardaPoint]:
        point = self._points.get(point_id)
        if point is None:
            logger.info("NardaPointRepository: narda_point_id=%s inconnu", point_id)
            return None
        self._uow.register(point)
        return point

    def list_by_scan(self, scan_id: UUID) -> List[NardaPoint]:
        points = [p for p in self._points.values() if p.scan_id == scan_id]
        for p in points:
            self._uow.register(p)
        return points
