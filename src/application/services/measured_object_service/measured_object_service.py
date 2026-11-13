"""
MeasuredObject Service — the measured_object use cases (see measured_object_service_intention.md).
"""

import logging
from typing import List

from application.services.measured_object_service.dtos.measured_object_dto import MeasuredObjectDTO, MeasuredObjectRegistrationDTO
from application.services.measured_object_service.i_api_measured_object_service import IApiMeasuredObjectService
from application.services.measured_object_service.measured_object_service_errors import (
    MeasuredObjectNameBlank,
    MeasuredObjectRegistryUnavailable,
    MeasuredObjectServiceError,
)
from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from domain.measured_object_registry.errors.measured_object_name_blank_error import MeasuredObjectNameBlankError
from domain.measured_object_registry.measured_object_registry import MeasuredObjectRegistry
from domain.measured_object_registry.repositories.i_measured_object_repository import IMeasuredObjectRepository
from domain.shared_kernel.events.i_domain_event_bus.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.operation_result import OperationResult

MEASURED_OBJECT_REGISTERED_TOPIC = "measuredobjectregistered"

logger = logging.getLogger(__name__)


def _dto(measured_object: MeasuredObject) -> MeasuredObjectDTO:
    return MeasuredObjectDTO(measured_object_id=str(measured_object.measured_object_id), name=measured_object.name)


class MeasuredObjectService(IApiMeasuredObjectService):
    def __init__(self, repository: IMeasuredObjectRepository, event_bus: IDomainEventBus) -> None:
        self._repository = repository
        self._event_bus = event_bus

    # -- queries ------------------------------------------------------------------

    def list_measured_objects(self) -> OperationResult[List[MeasuredObjectDTO], MeasuredObjectServiceError]:
        found = self._repository.find_all()
        if found.is_failure:
            logger.warning("MeasuredObjectService: measured_objects unavailable: %s", found.error)
            return OperationResult.fail(MeasuredObjectRegistryUnavailable(reason=found.error))
        return OperationResult.ok([_dto(o) for o in sorted(found.value, key=lambda o: o.name.casefold())])

    # -- commands -----------------------------------------------------------------

    def register_measured_object(self, name: str) -> OperationResult[MeasuredObjectRegistrationDTO, MeasuredObjectServiceError]:
        logger.info("MeasuredObjectService: Command register_measured_object name=%r", name)
        found = self._repository.find_all()
        if found.is_failure:
            logger.warning("MeasuredObjectService: registration refused, registry unavailable: %s", found.error)
            return OperationResult.fail(MeasuredObjectRegistryUnavailable(reason=found.error))

        registry = MeasuredObjectRegistry.reconstitute(found.value)
        try:
            measured_object, created = registry.register(name)
        except MeasuredObjectNameBlankError as error:
            logger.info("MeasuredObjectService: registration refused: %s", error)
            return OperationResult.fail(MeasuredObjectNameBlank())

        if not created:
            logger.info(
                "MeasuredObjectService: %r is already registered as measured_object_id=%s name=%r. Doing nothing.",
                name, measured_object.measured_object_id, measured_object.name,
            )
            return OperationResult.ok(MeasuredObjectRegistrationDTO(measured_object=_dto(measured_object), already_registered=True))

        saved = self._repository.add(measured_object)
        if saved.is_failure:
            logger.warning("MeasuredObjectService: measured_object %r not saved: %s", measured_object.name, saved.error)
            return OperationResult.fail(MeasuredObjectRegistryUnavailable(reason=saved.error))
        for event in registry.domain_events:
            self._event_bus.publish(type(event).__name__.lower(), event)
        logger.info("MeasuredObjectService: measured_object registered measured_object_id=%s name=%r", measured_object.measured_object_id, measured_object.name)
        return OperationResult.ok(MeasuredObjectRegistrationDTO(measured_object=_dto(measured_object), already_registered=False))
