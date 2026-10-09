"""SpectralAnalysisService (see spectral_analysis_service_intention.md)."""

import logging
from collections import deque
from datetime import datetime
from typing import Deque, Dict, Optional, Tuple
from uuid import UUID

from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.signal_processing.events.aefi_corrected_field_sample_acquired.aefi_corrected_field_sample_acquired import (
    AefiCorrectedFieldSampleAcquired,
)
from domain.signal_processing.events.spectral_analysis_result_updated.spectral_analysis_result_updated import (
    SpectralAnalysisResultUpdated,
)
from domain.signal_processing.services.spectral_analysis_calculator.spectral_analysis_calculator import (
    SpectralAnalysisCalculator,
)

from .dtos.spectral_analysis_dtos import SetWindowDurationDTO
from .i_api_spectral_analysis_service import IApiSpectralAnalysisService

logger = logging.getLogger(__name__)


class SpectralAnalysisService(IApiSpectralAnalysisService):
    """
    Maintains a time-bounded buffer (by duration, not by sample count) of
    corrected field samples and recomputes the FFT amplitude spectrum
    (SpectralAnalysisCalculator, a pure domain service) every time a new
    sample arrives once the window is full. See intention.md.
    """

    def __init__(self, event_bus: IDomainEventBus, window_duration_s: float):
        self._event_bus = event_bus
        self._window_duration_s = window_duration_s
        self._buffer: Deque[Tuple[datetime, Dict[str, float]]] = deque()
        self._current_acquisition_id: Optional[UUID] = None
        # Tracked independently from the (trimmed) buffer span: once the buffer has
        # been trimmed to <= window_duration_s, its span is *always* strictly below
        # window_duration_s again on the next sample (discrete sampling never lands
        # exactly on the boundary) — re-deriving "is the window full?" from the
        # post-trim span would therefore latch into never-compute after the first
        # trim. This flag is a one-way latch set once the window has genuinely been
        # filled at least once, reset only on acquisition change / window resize.
        self._window_filled = False
        self._first_sample_time: Optional[datetime] = None
        event_bus.subscribe("aeficorrectedfieldsampleacquired", self._on_corrected_sample)

    def _on_corrected_sample(self, event: AefiCorrectedFieldSampleAcquired) -> None:
        if event.acquisition_id != self._current_acquisition_id:
            logger.info(
                "SpectralAnalysisService: acquisition_id changed to %s. Resetting buffer.",
                event.acquisition_id,
            )
            self._reset_buffer()
            self._current_acquisition_id = event.acquisition_id

        m = event.sample
        timestamp = m.timestamp
        if self._first_sample_time is None:
            self._first_sample_time = timestamp
        self._buffer.append((timestamp, {
            "Ux In-Phase": m.field_x_in_phase, "Ux Quadrature": m.field_x_quadrature,
            "Uy In-Phase": m.field_y_in_phase, "Uy Quadrature": m.field_y_quadrature,
            "Uz In-Phase": m.field_z_in_phase, "Uz Quadrature": m.field_z_quadrature,
        }))

        while len(self._buffer) >= 2 and (
            self._buffer[-1][0] - self._buffer[0][0]
        ).total_seconds() > self._window_duration_s:
            self._buffer.popleft()

        if not self._window_filled:
            if (timestamp - self._first_sample_time).total_seconds() < self._window_duration_s:
                return
            self._window_filled = True

        if len(self._buffer) < 2:
            return

        result = SpectralAnalysisCalculator.compute(list(self._buffer), self._window_duration_s)
        self._event_bus.publish(
            "spectralanalysisresultupdated",
            SpectralAnalysisResultUpdated(acquisition_id=event.acquisition_id, result=result),
        )

    def set_window_duration(self, dto: SetWindowDurationDTO) -> None:
        logger.info("SpectralAnalysisService: Command set_window_duration seconds=%s", dto.seconds)
        self._window_duration_s = dto.seconds
        self._reset_buffer()

    def _reset_buffer(self) -> None:
        self._buffer.clear()
        self._first_sample_time = None
        self._window_filled = False

    def get_window_duration(self) -> float:
        return self._window_duration_s
