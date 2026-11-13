"""
MeasuredObject Service — the measured_object use cases (see measured_object_service_intention.md).
"""

import logging
from typing import List, Optional
from uuid import UUID

from application.measured_object_registry.measured_object_service.dtos.measured_object_dto import MeasuredObjectDTO, MeasuredObjectRegistrationDTO
from application.measured_object_registry.measured_object_service.i_api_measured_object_service import IApiMeasuredObjectService
from application.measured_object_registry.measured_object_service.measured_object_service_errors import (
    MeasuredObjectNameBlank,
    MeasuredObjectNameTaken,
    MeasuredObjectNotFound,
    MeasuredObjectRegistryUnavailable,
    MeasuredObjectServiceError,
)
from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from domain.measured_object_registry.errors.measured_object_name_blank_error import MeasuredObjectNameBlankError
from domain.measured_object_registry.errors.measured_object_name_taken_error import MeasuredObjectNameTakenError
from domain.measured_object_registry.errors.measured_object_not_found_error import MeasuredObjectNotFoundError
from domain.measured_object_registry.measured_object_registry import MeasuredObjectRegistry
from domain.measured_object_registry.repositories.i_measured_object_repository import IMeasuredObjectRepository
from domain.shared_kernel.events.i_domain_event_bus.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.operation_result import OperationResult

MEASURED_OBJECT_REGISTERED_TOPIC = "measuredobjectregistered"
MEASURED_OBJECT_RENAMED_TOPIC = "measuredobjectrenamed"
MEASURED_OBJECT_DELETED_TOPIC = "measuredobjectdeleted"

logger = logging.getLogger(__name__)


def _dto(measured_object: MeasuredObject) -> MeasuredObjectDTO:
    return MeasuredObjectDTO(measured_object_id=str(measured_object.measured_object_id), name=measured_object.name)


def _uuid(measured_object_id: str) -> Optional[UUID]:
    try:
        return UUID(measured_object_id)
    except (TypeError, ValueError):
        return None


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

    def rename_measured_object(self, measured_object_id: str, name: str) -> OperationResult[MeasuredObjectDTO, MeasuredObjectServiceError]:
        logger.info("MeasuredObjectService: Command rename_measured_object measured_object_id=%s name=%r", measured_object_id, name)
        identity = _uuid(measured_object_id)
        if identity is None:
            logger.info("MeasuredObjectService: rename refused, measured_object_id=%r is not an identity", measured_object_id)
            return OperationResult.fail(MeasuredObjectNotFound(measured_object_id=measured_object_id))
        found = self._repository.find_all()
        if found.is_failure:
            logger.warning("MeasuredObjectService: rename refused, registry unavailable: %s", found.error)
            return OperationResult.fail(MeasuredObjectRegistryUnavailable(reason=found.error))

        registry = MeasuredObjectRegistry.reconstitute(found.value)
        try:
            renamed, changed = registry.rename(identity, name)
        except MeasuredObjectNotFoundError as error:
            logger.info("MeasuredObjectService: rename refused: %s", error)
            return OperationResult.fail(MeasuredObjectNotFound(measured_object_id=measured_object_id))
        except MeasuredObjectNameTakenError as error:
            logger.info("MeasuredObjectService: rename refused measured_object_id=%s: %s", measured_object_id, error)
            return OperationResult.fail(MeasuredObjectNameTaken(message=str(error)))
        except MeasuredObjectNameBlankError as error:
            logger.info("MeasuredObjectService: rename refused measured_object_id=%s: %s", measured_object_id, error)
            return OperationResult.fail(MeasuredObjectNameBlank())

        if not changed:
            logger.info("MeasuredObjectService: measured_object_id=%s is already named %r. Doing nothing.", measured_object_id, renamed.name)
            return OperationResult.ok(_dto(renamed))
        return self._save_and_publish(registry, _dto(renamed), "renamed")

    def delete_measured_object(self, measured_object_id: str) -> OperationResult[MeasuredObjectDTO, MeasuredObjectServiceError]:
        logger.info("MeasuredObjectService: Command delete_measured_object measured_object_id=%s", measured_object_id)
        identity = _uuid(measured_object_id)
        if identity is None:
            logger.info("MeasuredObjectService: deletion refused, measured_object_id=%r is not an identity", measured_object_id)
            return OperationResult.fail(MeasuredObjectNotFound(measured_object_id=measured_object_id))
        found = self._repository.find_all()
        if found.is_failure:
            logger.warning("MeasuredObjectService: deletion refused, registry unavailable: %s", found.error)
            return OperationResult.fail(MeasuredObjectRegistryUnavailable(reason=found.error))

        registry = MeasuredObjectRegistry.reconstitute(found.value)
        try:
            removed = registry.delete(identity)
        except MeasuredObjectNotFoundError as error:
            logger.info("MeasuredObjectService: deletion refused: %s", error)
            return OperationResult.fail(MeasuredObjectNotFound(measured_object_id=measured_object_id))
        return self._save_and_publish(registry, _dto(removed), "deleted")

    def _save_and_publish(
        self, registry: MeasuredObjectRegistry, outcome: MeasuredObjectDTO, done: str,
    ) -> OperationResult[MeasuredObjectDTO, MeasuredObjectServiceError]:
        saved = self._repository.save_all(registry.measured_objects)
        if saved.is_failure:
            logger.warning("MeasuredObjectService: measured_object_id=%s not %s, registry not saved: %s", outcome.measured_object_id, done, saved.error)
            return OperationResult.fail(MeasuredObjectRegistryUnavailable(reason=saved.error))
        for event in registry.domain_events:
            self._event_bus.publish(type(event).__name__.lower(), event)
        logger.info("MeasuredObjectService: measured_object %s measured_object_id=%s name=%r", done, outcome.measured_object_id, outcome.name)
        return OperationResult.ok(outcome)
