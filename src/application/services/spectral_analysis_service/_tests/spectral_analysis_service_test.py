from datetime import datetime, timedelta, timezone
from uuid import uuid4

from tool.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.events.in_memory_event_bus import InMemoryEventBus

from application.services.spectral_analysis_service.spectral_analysis_service import SpectralAnalysisService
from application.services.spectral_analysis_service.dtos.spectral_analysis_dtos import SetWindowDurationDTO

from domain.signal_processing.events.aefi_corrected_field_sample_acquired.aefi_corrected_field_sample_acquired import (
    AefiCorrectedFieldSampleAcquired,
)
from domain.signal_processing.value_objects.aefi_corrected_field_measurement.aefi_corrected_field_measurement import (
    AefiCorrectedFieldMeasurement,
)

BASE_TIME = datetime(2026, 10, 9, tzinfo=timezone.utc)


def make_field_sample(t: datetime, value: float = 1.0) -> AefiCorrectedFieldMeasurement:
    return AefiCorrectedFieldMeasurement(
        field_x_in_phase=value, field_x_quadrature=value,
        field_y_in_phase=value, field_y_quadrature=value,
        field_z_in_phase=value, field_z_quadrature=value,
        timestamp=t,
    )


class TestSpectralAnalysisService(DiagramFriendlyTest):
    """Diagram-friendly test: SpectralAnalysisService buffers corrected field
    samples by duration and republishes SpectralAnalysisResultUpdated once the
    window is full, using a real InMemoryEventBus."""

    def setUp(self) -> None:
        super().setUp()
        self.event_bus = InMemoryEventBus()
        self.results = []
        self.event_bus.subscribe("spectralanalysisresultupdated", self.results.append)
        self.service = SpectralAnalysisService(self.event_bus, window_duration_s=1.0)

    def _publish(self, acquisition_id, index: int, t: datetime, value: float = 1.0) -> None:
        self.event_bus.publish(
            "aeficorrectedfieldsampleacquired",
            AefiCorrectedFieldSampleAcquired(
                acquisition_id=acquisition_id, sample_index=index, sample=make_field_sample(t, value)
            ),
        )

    def test_no_result_until_window_is_full(self):
        self.log_divider("Partial window")
        acquisition_id = uuid4()
        for i in range(5):
            self._publish(acquisition_id, i, BASE_TIME + timedelta(seconds=0.1 * i))

        self.assertEqual(self.results, [])

    def test_result_published_once_window_is_full(self):
        self.log_divider("Full window")
        acquisition_id = uuid4()
        for i in range(15):
            self._publish(acquisition_id, i, BASE_TIME + timedelta(seconds=0.1 * i))

        self.assertGreaterEqual(len(self.results), 1)
        result = self.results[-1].result
        self.assertIn("Ux In-Phase", result.amplitudes_by_channel)

    def test_acquisition_id_change_resets_buffer(self):
        self.log_divider("Acquisition change resets buffer")
        acquisition_id_1 = uuid4()
        for i in range(15):
            self._publish(acquisition_id_1, i, BASE_TIME + timedelta(seconds=0.1 * i))
        self.results.clear()

        acquisition_id_2 = uuid4()
        self._publish(acquisition_id_2, 0, BASE_TIME + timedelta(seconds=100.0))

        # Only one sample now sits in the (reset) buffer -> no result despite
        # the large elapsed time relative to the first acquisition.
        self.assertEqual(self.results, [])

    def test_set_window_duration_clears_buffer(self):
        self.log_divider("set_window_duration clears buffer")
        acquisition_id = uuid4()
        for i in range(10):
            self._publish(acquisition_id, i, BASE_TIME + timedelta(seconds=0.1 * i))

        self.service.set_window_duration(SetWindowDurationDTO(seconds=2.0))

        self.assertEqual(self.service.get_window_duration(), 2.0)
        self.results.clear()
        self._publish(acquisition_id, 10, BASE_TIME + timedelta(seconds=1.0))

        self.assertEqual(self.results, [])  # buffer was cleared, only 1 sample now
