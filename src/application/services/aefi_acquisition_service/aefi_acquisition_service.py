"""
Continuous Acquisition Application Service

Responsibility:
- Thin use case that validates configuration (later) and delegates to
  the IAefiAcquisitionExecutor port.
"""

from __future__ import annotations

from .ports.i_aefi_acquisition_executor import IAefiAcquisitionExecutor
from .dtos.aefi_acquisition_dtos import AefiAcquisitionConfig
from application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort


class AefiAcquisitionService:
    """
    Application service for continuous acquisition.

    For now it is intentionally minimal: it just forwards calls to the
    configured executor. Later we can add simple validation or mapping
    from UI DTOs.
    """

    def __init__(self, executor: IAefiAcquisitionExecutor, acquisition_port: IAcquisitionPort) -> None:
        self._executor = executor
        self._acquisition_port = acquisition_port

    def start_acquisition(self, config: AefiAcquisitionConfig) -> None:
        self._executor.start(config, self._acquisition_port)

    def stop_acquisition(self) -> None:
        self._executor.stop()

    def is_acquisition_running(self) -> bool:
        return self._executor.is_running()


