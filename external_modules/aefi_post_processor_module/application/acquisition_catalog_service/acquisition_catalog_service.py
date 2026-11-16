"""
Acquisition catalog service — the acquisitions of an export and their state (see acquisition_catalog_service_intention.md).
"""

import logging
from typing import Dict, Tuple

from ...domain.acquisition_record.repositories.i_acquisition_repository import IAcquisitionRepository
from .dtos.acquisition_outcome_dto import AcquisitionOutcomeDTO
from .dtos.acquisition_status_dto import FAILED, PROCESSED, TO_RECOMPUTE, AcquisitionStatusDTO
from .dtos.list_acquisitions_dto import ListAcquisitionsDTO
from .i_api_acquisition_catalog_service import IApiAcquisitionCatalogService

logger = logging.getLogger(__name__)


class AcquisitionCatalogService(IApiAcquisitionCatalogService):
    def __init__(self, repository: IAcquisitionRepository):
        self._repository = repository
        self._failures: Dict[str, str] = {}

    def list_acquisitions(self, request: ListAcquisitionsDTO) -> Tuple[AcquisitionStatusDTO, ...]:
        statuses = []
        for record in self._repository.list_acquisitions(request.export_folder):
            reason = record.recalculation_reason(request.force)
            failure = self._failures.get(record.name)
            if failure is not None:
                state = FAILED
            elif reason is not None:
                state = TO_RECOMPUTE
            else:
                state = PROCESSED
            statuses.append(AcquisitionStatusDTO(
                name=record.name, kind=record.kind, folder=record.folder, csv_file=record.csv_file,
                acquisition_file=record.acquisition_file, state=state,
                reason=reason if state == TO_RECOMPUTE else None, failure_message=failure,
            ))
        logger.info(
            "catalog.listed export=%s acquisitions=%d to_recompute=%d failed=%d",
            request.export_folder, len(statuses),
            sum(1 for s in statuses if s.state == TO_RECOMPUTE), sum(1 for s in statuses if s.state == FAILED),
        )
        return tuple(statuses)

    def report_outcome(self, outcome: AcquisitionOutcomeDTO) -> None:
        if outcome.succeeded:
            self._failures.pop(outcome.name, None)
        else:
            self._failures[outcome.name] = outcome.message
            logger.warning("catalog.failure_remembered acquisition=%s message=%s", outcome.name, outcome.message)
