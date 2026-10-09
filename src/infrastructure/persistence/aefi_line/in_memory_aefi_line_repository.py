import logging
from typing import Dict, List, Optional
from uuid import UUID

from application.services.scan_application_service.ports.i_unit_of_work import IUnitOfWork
from domain.aefi_line.aefi_line import AefiLine
from domain.aefi_line.repositories.i_aefi_line_repository import IAefiLineRepository
from domain.aefi_line.value_objects.aefi_line_id.aefi_line_id import AefiLineId

logger = logging.getLogger(__name__)


class InMemoryAefiLineRepository(IAefiLineRepository):
    """Repository mono-processus sans DB ; chaque agregat vu est enregistre aupres de l'UoW."""

    def __init__(self, uow: IUnitOfWork):
        self._uow = uow
        self._lines: Dict[AefiLineId, AefiLine] = {}

    def add(self, line: AefiLine) -> None:
        logger.info(
            "AefiLineRepository: add aefi_line_id=%s scan_id=%s line_index=%s", line.id, line.scan_id, line.line_index
        )
        self._lines[line.id] = line
        self._uow.register(line)

    def get(self, line_id: AefiLineId) -> Optional[AefiLine]:
        line = self._lines.get(line_id)
        if line is None:
            logger.info("AefiLineRepository: aefi_line_id=%s inconnu", line_id)
            return None
        self._uow.register(line)
        return line

    def list_by_scan(self, scan_id: UUID) -> List[AefiLine]:
        lines = sorted((l for l in self._lines.values() if l.scan_id == scan_id), key=lambda l: l.line_index)
        for line in lines:
            self._uow.register(line)
        return lines
