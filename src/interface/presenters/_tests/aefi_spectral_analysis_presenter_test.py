"""Unit tests for AefiSpectralAnalysisPresenter (see aefi_spectral_analysis_presenter.py)."""

import unittest
from datetime import datetime, timezone
from uuid import uuid4

from application.services.spectral_analysis_service.dtos.spectral_analysis_dtos import SetWindowDurationDTO
from application.services.spectral_analysis_service.i_api_spectral_analysis_service import (
    IApiSpectralAnalysisService,
)
from domain.signal_processing.events.spectral_analysis_result_updated.spectral_analysis_result_updated import (
    SpectralAnalysisResultUpdated,
)
from domain.signal_processing.value_objects.spectral_analysis_result.spectral_analysis_result import (
    SpectralAnalysisResult,
)
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from interface.presenters.aefi_spectral_analysis_presenter import AefiSpectralAnalysisPresenter
from interface.view_models.aefi_spectral_analysis_view_model import AefiSpectralAnalysisViewModel

WINDOW_START = datetime(2026, 10, 9, 0, 0, 0, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 10, 9, 0, 0, 2, tzinfo=timezone.utc)


class FakeSpectralAnalysisService(IApiSpectralAnalysisService):
    """Hand-written stub tracking calls (Fake, not Mock, per this repo's test standard)."""

    def __init__(self):
        self.set_window_duration_calls = []
        self._window_duration_s = 2.0

    def set_window_duration(self, dto: SetWindowDurationDTO) -> None:
        self.set_window_duration_calls.append(dto)
        self._window_duration_s = dto.seconds

    def get_window_duration(self) -> float:
        return self._window_duration_s


def make_result() -> SpectralAnalysisResult:
    return SpectralAnalysisResult(
        frequencies_hz=(0.0, 1.0, 2.0),
        amplitudes_by_channel={
            "Ux In-Phase": (0.1, 0.2, 0.3),
            "Ux Quadrature": (0.0, 0.0, 0.0),
            "Uy In-Phase": (0.0, 0.0, 0.0),
            "Uy Quadrature": (0.0, 0.0, 0.0),
            "Uz In-Phase": (0.0, 0.0, 0.0),
            "Uz Quadrature": (0.0, 0.0, 0.0),
        },
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        sample_count=300,
    )


class TestAefiSpectralAnalysisPresenter(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.service = FakeSpectralAnalysisService()
        self.presenter = AefiSpectralAnalysisPresenter(self.service, self.event_bus)
        self.received_spectra = []
        self.presenter.spectrum_updated.connect(self.received_spectra.append)

    def test_result_updated_event_emits_translated_view_model(self):
        self.event_bus.publish(
            "spectralanalysisresultupdated",
            SpectralAnalysisResultUpdated(acquisition_id=uuid4(), result=make_result()),
        )

        self.assertEqual(len(self.received_spectra), 1)
        vm = self.received_spectra[0]
        self.assertIsInstance(vm, AefiSpectralAnalysisViewModel)
        self.assertEqual(vm.frequencies_hz, [0.0, 1.0, 2.0])
        self.assertEqual(vm.amplitudes_by_channel["Ux In-Phase"], [0.1, 0.2, 0.3])
        self.assertEqual(vm.window_start_iso, WINDOW_START.isoformat())
        self.assertEqual(vm.window_end_iso, WINDOW_END.isoformat())
        self.assertEqual(vm.sample_count, 300)

    def test_on_window_duration_changed_delegates_to_service(self):
        self.presenter.on_window_duration_changed(5.0)

        self.assertEqual(len(self.service.set_window_duration_calls), 1)
        self.assertEqual(self.service.set_window_duration_calls[0].seconds, 5.0)

    def test_shutdown_unsubscribes_result_updated_topic(self):
        self.presenter.shutdown()

        self.event_bus.publish(
            "spectralanalysisresultupdated",
            SpectralAnalysisResultUpdated(acquisition_id=uuid4(), result=make_result()),
        )

        self.assertEqual(self.received_spectra, [])


if __name__ == "__main__":
    unittest.main()
