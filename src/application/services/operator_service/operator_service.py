"""
Operator Service — the operator use cases (see operator_service_intention.md).
"""

import logging
from typing import List

from application.services.operator_service.dtos.operator_dto import OperatorDTO, OperatorRegistrationDTO
from application.services.operator_service.i_api_operator_service import IApiOperatorService
from application.services.operator_service.operator_service_errors import (
    OperatorNameBlank,
    OperatorRegistryUnavailable,
    OperatorServiceError,
)
from domain.operator_registry.entities.operator.operator import Operator
from domain.operator_registry.errors.operator_name_blank_error import OperatorNameBlankError
from domain.operator_registry.operator_registry import OperatorRegistry
from domain.operator_registry.repositories.i_operator_repository import IOperatorRepository
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.operation_result import OperationResult

OPERATOR_REGISTERED_TOPIC = "operatorregistered"

logger = logging.getLogger(__name__)


def _dto(operator: Operator) -> OperatorDTO:
    return OperatorDTO(operator_id=str(operator.operator_id), name=operator.name)


class OperatorService(IApiOperatorService):
    def __init__(self, repository: IOperatorRepository, event_bus: IDomainEventBus) -> None:
        self._repository = repository
        self._event_bus = event_bus

    # -- queries ------------------------------------------------------------------

    def list_operators(self) -> OperationResult[List[OperatorDTO], OperatorServiceError]:
        found = self._repository.find_all()
        if found.is_failure:
            logger.warning("OperatorService: operators unavailable: %s", found.error)
            return OperationResult.fail(OperatorRegistryUnavailable(reason=found.error))
        return OperationResult.ok([_dto(o) for o in sorted(found.value, key=lambda o: o.name.casefold())])

    # -- commands -----------------------------------------------------------------

    def register_operator(self, name: str) -> OperationResult[OperatorRegistrationDTO, OperatorServiceError]:
        logger.info("OperatorService: Command register_operator name=%r", name)
        found = self._repository.find_all()
        if found.is_failure:
            logger.warning("OperatorService: registration refused, registry unavailable: %s", found.error)
            return OperationResult.fail(OperatorRegistryUnavailable(reason=found.error))

        registry = OperatorRegistry.reconstitute(found.value)
        try:
            operator, created = registry.register(name)
        except OperatorNameBlankError as error:
            logger.info("OperatorService: registration refused: %s", error)
            return OperationResult.fail(OperatorNameBlank())

        if not created:
            logger.info(
                "OperatorService: %r is already registered as operator_id=%s name=%r. Doing nothing.",
                name, operator.operator_id, operator.name,
            )
            return OperationResult.ok(OperatorRegistrationDTO(operator=_dto(operator), already_registered=True))

        saved = self._repository.add(operator)
        if saved.is_failure:
            logger.warning("OperatorService: operator %r not saved: %s", operator.name, saved.error)
            return OperationResult.fail(OperatorRegistryUnavailable(reason=saved.error))
        for event in registry.domain_events:
            self._event_bus.publish(type(event).__name__.lower(), event)
        logger.info("OperatorService: operator registered operator_id=%s name=%r", operator.operator_id, operator.name)
        return OperationResult.ok(OperatorRegistrationDTO(operator=_dto(operator), already_registered=False))
