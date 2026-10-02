"""
Continuous Acquisition Application Service

Responsibility:
- Thin use case that delegates start/stop of the continuous acquisition to
  the IAefiAcquisitionExecutor port.
- Single owner of the stream (scan, automatic calibration, throughput
  characterization...): while held, Start/Stop from anyone else is refused.
"""

from __future__ import annotations

import logging
from typing import Optional

from .ports.i_aefi_acquisition_executor import IAefiAcquisitionExecutor
from .dtos.aefi_acquisition_dtos import AefiAcquisitionConfig
from .i_api_aefi_acquisition_service import IApiAefiAcquisitionService
from application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort
from application.shared.exclusive_control.exclusive_control import ExclusiveControl
from domain.shared_kernel.events.aefi_acquisition_control_changed.aefi_acquisition_control_changed import (
    AefiAcquisitionControlChanged,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.operation_result import OperationResult

AEFI_ACQUISITION_CONTROL_CHANGED_TOPIC = "aefiacquisitioncontrolchanged"

logger = logging.getLogger(__name__)


class AefiAcquisitionService(IApiAefiAcquisitionService):
    """
    Application service for continuous acquisition.
    """

    def __init__(
        self,
        executor: IAefiAcquisitionExecutor,
        acquisition_port: IAcquisitionPort,
        event_bus: Optional[IDomainEventBus] = None,
    ) -> None:
        """`event_bus`: where the change of stream owner is published (None:
        not published — tests that do not watch it)."""
        self._executor = executor
        self._acquisition_port = acquisition_port
        self._control = ExclusiveControl(
            "flux d'acquisition",
            lambda controller: event_bus is not None and event_bus.publish(
                AEFI_ACQUISITION_CONTROL_CHANGED_TOPIC, AefiAcquisitionControlChanged(controller=controller)
            ),
        )

    # -- control (single owner) ---------------------------------------------------

    def take_control(self, controller: str) -> OperationResult[None, str]:
        logger.info("AefiAcquisitionService: Command take_control controller=%s", controller)
        return self._control.take(controller)

    def release_control(self, controller: str) -> None:
        self._control.release(controller)

    def get_controller(self) -> Optional[str]:
        return self._control.controller

    # -- commands -----------------------------------------------------------------

    def start_acquisition(
        self, config: AefiAcquisitionConfig, controller: Optional[str] = None
    ) -> OperationResult[None, str]:
        logger.info(
            "AefiAcquisitionService: Command start_acquisition max_duration_s=%s controller=%s",
            config.max_duration_s, controller,
        )
        refusal = self._control.refusal(controller, "start_acquisition")
        if refusal is not None:
            return OperationResult.fail(refusal)
        self._executor.start(config, self._acquisition_port)
        return OperationResult.ok(None)

    def stop_acquisition(self, controller: Optional[str] = None) -> OperationResult[None, str]:
        logger.info("AefiAcquisitionService: Command stop_acquisition controller=%s", controller)
        refusal = self._control.refusal(controller, "stop_acquisition")
        if refusal is not None:
            return OperationResult.fail(refusal)
        self._executor.stop()
        return OperationResult.ok(None)

    def is_acquisition_running(self) -> bool:
        return self._executor.is_running()
