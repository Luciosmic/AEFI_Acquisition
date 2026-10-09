"""End-to-end test: raw AefiVoltageSampleAcquired -> AefiSignalProcessingService
(correction + sensor->source transform) -> SpectralAnalysisService (FFT), sharing
one InMemoryEventBus and a real TransformationService. Verifies both the happy
path (a known sine injected in the raw stream surfaces as a spectral peak at the
same frequency) and the invariant-rejection path (incomplete calibration drops
the sample silently through the whole pipeline — neither AefiSampleCorrected nor
SpectralAnalysisResultUpdated is published for it)."""

import math
import random
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from tool.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.events.in_memory_event_bus import InMemoryEventBus

from application.services.aefi_signal_processing_service.aefi_signal_processing_service import (
    AefiSignalProcessingService,
)
from application.services.spectral_analysis_service.spectral_analysis_service import SpectralAnalysisService
from application.services.transformation_service.transformation_service import TransformationService

from domain.shared_kernel.events.aefi_voltage_sample_acquired.aefi_voltage_sample_acquired import (
    AefiVoltageSampleAcquired,
)
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement

SIGNAL_FREQUENCY_HZ = 10.0
SAMPLE_RATE_HZ = 150.0  # Round-trip FTDI/MCU order of magnitude (ADR-003).
WINDOW_DURATION_S = 1.0
JITTER_S = 0.0005  # +/- 0.5 ms, consistent with ADR-003.
EPOCH = datetime(2026, 10, 9, tzinfo=timezone.utc)


def make_measurement(t: float) -> AefiVoltageMeasurement:
    value = math.sin(2 * math.pi * SIGNAL_FREQUENCY_HZ * t)
    return AefiVoltageMeasurement(
        voltage_x_in_phase=value, voltage_x_quadrature=value,
        voltage_y_in_phase=value, voltage_y_quadrature=value,
        voltage_z_in_phase=value, voltage_z_quadrature=value,
        timestamp=EPOCH + timedelta(seconds=t),
    )


class TestAefiSignalCorrectionToSpectralAnalysisIntegration(DiagramFriendlyTest):

    def setUp(self) -> None:
        super().setUp()
        self.event_bus = InMemoryEventBus()
        self.transformation_service = TransformationService()
        self.signal_processing_service = AefiSignalProcessingService(self.event_bus, self.transformation_service)
        self.spectral_analysis_service = SpectralAnalysisService(self.event_bus, window_duration_s=WINDOW_DURATION_S)

        self.corrected_events = []
        self.spectral_results = []
        self.event_bus.subscribe("aefisamplecorrected", self.corrected_events.append)
        self.event_bus.subscribe("spectralanalysisresultupdated", self.spectral_results.append)

    def _publish_raw_burst(self, acquisition_id, n_samples: int) -> None:
        rng = random.Random(42)
        dt_nominal = 1.0 / SAMPLE_RATE_HZ
        t = 0.0
        for i in range(n_samples):
            self.event_bus.publish(
                "aefivoltagesampleacquired",
                AefiVoltageSampleAcquired(
                    acquisition_id=acquisition_id, sample_index=i, sample=make_measurement(t)
                ),
            )
            t += dt_nominal + rng.uniform(-JITTER_S, JITTER_S)

    def test_known_sine_propagates_to_a_spectral_peak_at_the_injected_frequency(self):
        self.log_divider("Raw sine -> corrected -> FFT peak")
        acquisition_id = uuid4()
        n_samples = int(SAMPLE_RATE_HZ * (WINDOW_DURATION_S + 0.5))

        self.log_interaction(
            "Test", "PUBLISH", "EventBus",
            f"Publish {n_samples} raw AefiVoltageSampleAcquired (sine @ {SIGNAL_FREQUENCY_HZ} Hz + jitter)",
        )
        self._publish_raw_burst(acquisition_id, n_samples)

        self.assertEqual(len(self.corrected_events), n_samples)
        self.assertGreaterEqual(len(self.spectral_results), 1)

        last_result = self.spectral_results[-1].result
        freqs = last_result.frequencies_hz
        amplitudes = last_result.amplitudes_by_channel["Ux In-Phase"]

        # Ignore the DC bin (freq == 0) when looking for the injected tone.
        peak_amplitude, peak_frequency = max(
            ((amp, f) for amp, f in zip(amplitudes, freqs) if f > 0),
            key=lambda pair: pair[0],
        )

        self.log_interaction(
            "Test", "ASSERT", "SpectralAnalysisResult",
            "Peak frequency matches the injected sine",
            expect=SIGNAL_FREQUENCY_HZ, got=peak_frequency,
        )
        self.assertAlmostEqual(peak_frequency, SIGNAL_FREQUENCY_HZ, delta=1.0)
        self.assertGreater(peak_amplitude, 0.0)

    def test_incomplete_calibration_rejects_sample_through_the_whole_pipeline(self):
        self.log_divider("Incomplete calibration rejects the sample end-to-end")
        acquisition_id = uuid4()
        # Enable phase correction without ever calibrating it: AefiCorrectedSample
        # must reject the sample (SignalCorrectionCalibrationMissingError), caught
        # by AefiSignalProcessingService, which then publishes nothing downstream —
        # so SpectralAnalysisService never sees this sample either.
        self.signal_processing_service.set_phase_correction_enabled(True)

        self.event_bus.publish(
            "aefivoltagesampleacquired",
            AefiVoltageSampleAcquired(acquisition_id=acquisition_id, sample_index=0, sample=make_measurement(0.0)),
        )

        self.assertEqual(self.corrected_events, [])
        self.assertEqual(self.spectral_results, [])
