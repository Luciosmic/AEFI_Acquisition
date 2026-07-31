import time
import unittest
from typing import List

from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.electric_field_probe_acquisition_executor import (
    ElectricFieldProbeAcquisitionExecutor,
)
from infrastructure.hardware.narda_ep600.fake.fake_electric_field_probe_adapter import (
    FakeElectricFieldProbeAdapter,
)
from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import (
    ElectricFieldProbeAcquisitionConfig,
)
from domain.electric_field_probe.events.electric_field_probe_frequency_correction_changed.electric_field_probe_frequency_correction_changed import (
    ElectricFieldProbeFrequencyCorrectionChanged,
)

FREQUENCY_CORRECTION_CHANGED_TOPIC = "electricfieldprobefrequencycorrectionchanged"


class TestElectricFieldProbeAcquisitionExecutorFrequencyCorrection(unittest.TestCase):
    def setUp(self) -> None:
        self.probe_port = FakeElectricFieldProbeAdapter(noise_std=0.0)
        self.probe_port.connect()
        self.event_bus = InMemoryEventBus()
        self.events: List[ElectricFieldProbeFrequencyCorrectionChanged] = []
        self.event_bus.subscribe(FREQUENCY_CORRECTION_CHANGED_TOPIC, self.events.append)
        self.executor = ElectricFieldProbeAcquisitionExecutor(self.event_bus)
        self.config = ElectricFieldProbeAcquisitionConfig(max_duration_s=None)

    def tearDown(self) -> None:
        self.executor.stop()

    def test_no_event_published_if_nothing_requested(self) -> None:
        self.executor.start(self.config, self.probe_port)
        time.sleep(0.1)
        self.executor.stop()

        assert len(self.events) == 0

    def test_correction_applied_once_without_restarting_thread(self) -> None:
        self.executor.start(self.config, self.probe_port)
        thread_before = self.executor._thread

        self.executor.request_frequency_correction(50_000.0)
        time.sleep(0.2)

        assert self.executor._thread is thread_before
        assert len(self.events) == 1

        self.executor.stop()

    def test_stale_pending_frequency_not_replayed_on_restart(self) -> None:
        """A request made during a first run must not leak into a later
        start()/stop() cycle where nothing new was requested — see the
        70kHz-reverting-to-30kHz bug this guards against."""
        self.executor.start(self.config, self.probe_port)
        self.executor.request_frequency_correction(30_000.0)
        time.sleep(0.2)
        self.executor.stop()
        self.events.clear()

        self.executor.start(self.config, self.probe_port)
        time.sleep(0.2)
        self.executor.stop()

        assert len(self.events) == 0

    def test_event_published_with_expected_fields(self) -> None:
        self.executor.start(self.config, self.probe_port)

        self.executor.request_frequency_correction(50_000.0)
        time.sleep(0.2)
        self.executor.stop()

        assert len(self.events) == 1
        event = self.events[0]
        assert event.requested_hz == 50_000.0
        assert event.applied_hz == 50_000.0
        assert event.in_range is True
        assert event.error is None


if __name__ == "__main__":
    unittest.main()
