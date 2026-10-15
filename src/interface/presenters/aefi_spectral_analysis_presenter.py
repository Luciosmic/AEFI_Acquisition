"""
AEFI Spectral Analysis Presenter - Interface V2

Bridges between SpectralAnalysisService and AefiSpectralAnalysisPanel.
Translates SpectralAnalysisResultUpdated domain events into a Qt signal
carrying a rendering-oriented view model, and forwards the window-duration
control from the panel to the service.
"""

import logging

from PySide6.QtCore import QObject, Signal, Slot

from application.services.spectral_analysis_service.i_api_spectral_analysis_service import (
    IApiSpectralAnalysisService,
)
from application.services.spectral_analysis_service.dtos.spectral_analysis_dtos import SetWindowDurationDTO
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.signal_processing.events.spectral_analysis_result_updated.spectral_analysis_result_updated import (
    SpectralAnalysisResultUpdated,
)
from interface.view_models.aefi_spectral_analysis_view_model import AefiSpectralAnalysisViewModel

logger = logging.getLogger(__name__)


class AefiSpectralAnalysisPresenter(QObject):
    """
    Presenter for AefiSpectralAnalysisPanel.
    - Subscribes to SpectralAnalysisResultUpdated and emits spectrum_updated
      with a typed view model.
    - Forwards the panel's window-duration control to SpectralAnalysisService.
    """

    spectrum_updated = Signal(object)  # AefiSpectralAnalysisViewModel

    def __init__(self, service: IApiSpectralAnalysisService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
        self._event_bus = event_bus
        self._event_bus.subscribe("spectralanalysisresultupdated", self._on_result_updated)

    def _on_result_updated(self, event: SpectralAnalysisResultUpdated) -> None:
        result = event.result
        view_model = AefiSpectralAnalysisViewModel(
            frequencies_hz=list(result.frequencies_hz),
            amplitudes_by_channel={
                channel: list(amplitudes) for channel, amplitudes in result.amplitudes_by_channel.items()
            },
            window_start_iso=result.window_start.isoformat(),
            window_end_iso=result.window_end.isoformat(),
            sample_count=result.sample_count,
        )
        self.spectrum_updated.emit(view_model)

    @Slot(float)
    def on_window_duration_changed(self, seconds: float) -> None:
        logger.info("AefiSpectralAnalysisPresenter: Command set_window_duration seconds=%s", seconds)
        self._service.set_window_duration(SetWindowDurationDTO(seconds=seconds))

    def shutdown(self) -> None:
        """Cleanup resources."""
        if self._event_bus:
            self._event_bus.unsubscribe("spectralanalysisresultupdated", self._on_result_updated)
