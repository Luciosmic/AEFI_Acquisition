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

        self.event_bus.subscribe("fieldsampleacquired", self.samples.append)
        self.event_bus.subscribe(
            "electricfieldprobeconnectionchanged", self.connection_events.append
        )

        executor = ElectricFieldProbeAcquisitionExecutor(self.event_bus)
        self.service = ElectricFieldProbeService(
            executor=executor,
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

    def test_continuous_acquisition_short_burst(self) -> None:
        self.service.connect_probe()

        config = ElectricFieldProbeAcquisitionConfig(
            sample_rate_hz=20.0, max_duration_s=0.1
        )
        self.service.start_acquisition(config)

        time.sleep(0.2)

        self.service.stop_acquisition()

        assert len(self.samples) >= 1
        assert len(self.samples[0].sample.components) == 3


if __name__ == "__main__":
    import unittest

    unittest.main()
