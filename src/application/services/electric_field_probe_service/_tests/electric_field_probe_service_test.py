import time
from typing import List

from tool.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.electric_field_probe_acquisition_executor import (
    ElectricFieldProbeAcquisitionExecutor,
)

from application.services.electric_field_probe_service.electric_field_probe_service import (
    ElectricFieldProbeService,
)
from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import (
    ElectricFieldProbeAcquisitionConfig,
)

from infrastructure.hardware.narda_ep600.fake.fake_electric_field_probe_adapter import (
    FakeElectricFieldProbeAdapter,
)

from domain.electric_field_probe.events.field_sample_acquired.field_sample_acquired import (
    FieldSampleAcquired,
)
from domain.electric_field_probe.events.electric_field_probe_connection_changed.electric_field_probe_connection_changed import (
    ElectricFieldProbeConnectionChanged,
)
from domain.electric_field_probe.events.electric_field_probe_battery_refreshed.electric_field_probe_battery_refreshed import (
    ElectricFieldProbeBatteryRefreshed,
)
from domain.electric_field_probe.events.electric_field_probe_frequency_correction_changed.electric_field_probe_frequency_correction_changed import (
    ElectricFieldProbeFrequencyCorrectionChanged,
)
from domain.shared_kernel.events.excitation_frequency_changed.excitation_frequency_changed import (
    ExcitationFrequencyChanged,
)


class TestElectricFieldProbeService(DiagramFriendlyTest):
    """
    Diagram-friendly test for ElectricFieldProbeService.

    Goal:
    - Verify connect/disconnect never raise and publish connection events.
    - Verify a short continuous acquisition burst publishes FieldSampleAcquired.
    """

    def setUp(self) -> None:
        super().setUp()

        self.probe_port = FakeElectricFieldProbeAdapter(noise_std=0.0)
        self.event_bus = InMemoryEventBus()
        self.samples: List[FieldSampleAcquired] = []
        self.connection_events: List[ElectricFieldProbeConnectionChanged] = []

        self.battery_refreshed_events: List[ElectricFieldProbeBatteryRefreshed] = []
        self.frequency_correction_events: List[
            ElectricFieldProbeFrequencyCorrectionChanged
        ] = []

        self.event_bus.subscribe("fieldsampleacquired", self.samples.append)
        self.event_bus.subscribe(
            "electricfieldprobeconnectionchanged", self.connection_events.append
        )
        self.event_bus.subscribe(
            "electricfieldprobebatteryrefreshed", self.battery_refreshed_events.append
        )
        self.event_bus.subscribe(
            "electricfieldprobefrequencycorrectionchanged",
            self.frequency_correction_events.append,
        )

        self.executor = ElectricFieldProbeAcquisitionExecutor(self.event_bus)
        self.service = ElectricFieldProbeService(
            executor=self.executor,
            probe_port=self.probe_port,
            event_bus=self.event_bus,
        )

    def test_connect_probe_publishes_connected_event(self) -> None:
        self.service.connect_probe()

        assert len(self.connection_events) == 1
        assert self.connection_events[0].connected is True
        assert self.connection_events[0].probe is not None

    def test_connect_probe_failure_publishes_disconnected_event_without_raising(
        self,
    ) -> None:
        failing_port = FakeElectricFieldProbeAdapter(simulate_connection_failure=True)
        executor = ElectricFieldProbeAcquisitionExecutor(self.event_bus)
        service = ElectricFieldProbeService(
            executor=executor,
            probe_port=failing_port,
            event_bus=self.event_bus,
        )

        service.connect_probe()  # must not raise

        assert len(self.connection_events) == 1
        assert self.connection_events[0].connected is False
        assert self.connection_events[0].error is not None

    def test_refresh_battery_publishes_event_when_connected_and_idle(self) -> None:
        self.service.connect_probe()

        self.service.refresh_battery()

        assert len(self.battery_refreshed_events) == 1
        assert self.battery_refreshed_events[0].probe is not None

    def test_refresh_battery_noop_when_not_connected(self) -> None:
        self.service.refresh_battery()

        assert len(self.battery_refreshed_events) == 0

    def test_refresh_battery_refused_while_acquisition_running(self) -> None:
        self.service.connect_probe()
        config = ElectricFieldProbeAcquisitionConfig(max_duration_s=None)
        self.service.start_acquisition(config)

        self.service.refresh_battery()

        assert len(self.battery_refreshed_events) == 0

        self.service.stop_acquisition()

    def test_continuous_acquisition_short_burst(self) -> None:
        self.service.connect_probe()

        config = ElectricFieldProbeAcquisitionConfig(max_duration_s=0.1)
        self.service.start_acquisition(config)

        time.sleep(0.2)

        self.service.stop_acquisition()

        assert len(self.samples) >= 1
        assert len(self.samples[0].sample.components) == 3

    def test_connect_probe_applies_last_known_excitation_frequency(self) -> None:
        # Aucune ExcitationFrequencyChanged recue avant connexion -> 0.0 Hz par defaut
        # (miroir de ExcitationParameters.off().frequency), hors plage sonde (<10kHz).
        self.service.connect_probe()

        assert len(self.frequency_correction_events) == 1
        assert self.frequency_correction_events[0].requested_hz == 0.0
        assert self.frequency_correction_events[0].in_range is False

    def test_excitation_frequency_change_applies_directly_when_idle(self) -> None:
        self.service.connect_probe()
        self.frequency_correction_events.clear()

        self.event_bus.publish(
            "excitationfrequencychanged",
            ExcitationFrequencyChanged(frequency_hz=50_000.0),
        )

        assert len(self.frequency_correction_events) == 1
        assert self.frequency_correction_events[0].in_range is True
        assert self.frequency_correction_events[0].applied_hz == 50_000.0

    def test_excitation_frequency_change_out_of_range_below_10khz(self) -> None:
        self.service.connect_probe()
        self.frequency_correction_events.clear()

        self.event_bus.publish(
            "excitationfrequencychanged",
            ExcitationFrequencyChanged(frequency_hz=5_000.0),
        )

        assert len(self.frequency_correction_events) == 1
        assert self.frequency_correction_events[0].in_range is False
        assert self.frequency_correction_events[0].applied_hz is None

    def test_excitation_frequency_change_during_acquisition_uses_executor_without_stopping_stream(
        self,
    ) -> None:
        self.service.connect_probe()
        config = ElectricFieldProbeAcquisitionConfig(max_duration_s=None)
        self.service.start_acquisition(config)
        time.sleep(0.05)

        self.event_bus.publish(
            "excitationfrequencychanged",
            ExcitationFrequencyChanged(frequency_hz=50_000.0),
        )
        time.sleep(0.1)

        assert self.executor.is_running()
        assert len(self.samples) >= 1

        self.service.stop_acquisition()

        assert any(
            e.applied_hz == 50_000.0 for e in self.frequency_correction_events
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
