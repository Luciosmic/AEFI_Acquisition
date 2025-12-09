"""
Continuous Acquisition Application Service

Responsibility:
- Thin use case that validates configuration (later) and delegates to
  the IContinuousAcquisitionExecutor port.
"""

from __future__ import annotations

from application.ports.i_continuous_acquisition_executor import (
    IContinuousAcquisitionExecutor,
    ContinuousAcquisitionConfig,
)


class ContinuousAcquisitionService:
    """
    Application service for continuous acquisition.

    For now it is intentionally minimal: it just forwards calls to the
    configured executor. Later we can add simple validation or mapping
    from UI DTOs.
    """

    def __init__(self, executor: IContinuousAcquisitionExecutor) -> None:
        self._executor = executor

    def start_acquisition(self, config: ContinuousAcquisitionConfig) -> None:
        # TODO: add basic validation (sample_rate_hz > 0, etc.)
        self._executor.start(config)

    def stop_acquisition(self) -> None:
        self._executor.stop()


