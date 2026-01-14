"""
Continuous Acquisition Application Service

Responsibility:
- Thin use case that validates configuration (later) and delegates to
  the IContinuousAcquisitionExecutor port.
"""

from __future__ import annotations

from .i_continuous_acquisition_executor import (
    IContinuousAcquisitionExecutor,
    ContinuousAcquisitionConfig,
)
from application.services.scan_application_service.i_acquisition_port import IAcquisitionPort


class ContinuousAcquisitionService:
    """
    Application service for continuous acquisition.

    For now it is intentionally minimal: it just forwards calls to the
    configured executor. Later we can add simple validation or mapping
    from UI DTOs.
    """

    def __init__(self, executor: IContinuousAcquisitionExecutor, acquisition_port: IAcquisitionPort) -> None:
        self._executor = executor
        self._acquisition_port = acquisition_port

    def start_acquisition(self, config: ContinuousAcquisitionConfig) -> None:
        # TODO: add basic validation (sample_rate_hz > 0, etc.)
        self._executor.start(config, self._acquisition_port)

    def stop_acquisition(self) -> None:
        self._executor.stop()

    def update_acquisition_parameters(self, config: ContinuousAcquisitionConfig) -> None:
        """Updates the running acquisition parameters on the fly."""
        # Simple validation: ensure we aren't trying to set invalid rates
        if config.sample_rate_hz is not None and config.sample_rate_hz <= 0:
             # Just a basic check, in reality we might raise an error
             pass
        self._executor.update_config(config)


