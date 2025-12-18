import time
from typing import List

from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.events.in_memory_event_bus import InMemoryEventBus

from application.continuous_acquisition_service.continuous_acquisition_service import (
    ContinuousAcquisitionService,
)
from application.services.continuous_acquisition_service.i_continuous_acquisition_executor import (
    IContinuousAcquisitionExecutor,
    ContinuousAcquisitionConfig,
)

from infrastructure.execution.continuous_acquisition_executor import (
    ContinuousAcquisitionExecutor,
)
from infrastructure.tests.mock_ports import MockAcquisitionPort

from domain.models.aefi_device.events.continuous_acquisition_events import (
    ContinuousAcquisitionSampleAcquired,
)


class TestContinuousAcquisitionService(DiagramFriendlyTest):
    """
    Diagram-friendly test for ContinuousAcquisitionService + Executor.

    Goal:
    - Show a short continuous acquisition burst with a noisy/synthetic signal.
    - Verify that SampleAcquired events are published and received.
    """

    def setUp(self) -> None:
        super().setUp()

        self.log_interaction(
            "Test",
            "CREATE",
            "ContinuousAcquisitionService",
            "Setup service, executor, ports and event bus",
        )

        # Infrastructure mocks / adapters
        self.acquisition_port = MockAcquisitionPort()
        self.event_bus = InMemoryEventBus()
        self.samples: List[ContinuousAcquisitionSampleAcquired] = []

        # Subscribe to continuous acquisition events
        def on_sample(event: ContinuousAcquisitionSampleAcquired) -> None:
            data = {
                "acquisition_id": str(event.acquisition_id),
                "index": event.sample_index,
                "vx": event.sample.voltage_x_in_phase,
            }
            self.log_interaction(
                "EventBus",
                "RECEIVE",
                "Test",
                "Received ContinuousAcquisitionSampleAcquired",
                data=data,
            )
            self.samples.append(event)

        self.log_interaction(
            "Test",
            "SUBSCRIBE",
            "EventBus",
            "Subscribe to continuousacquisitionsampleacquired",
        )
        self.event_bus.subscribe("continuousacquisitionsampleacquired", on_sample)

        # Real executor wired on mocks
        self.executor = ContinuousAcquisitionExecutor(
            acquisition_port=self.acquisition_port,
            event_bus=self.event_bus,
        )
        self.service = ContinuousAcquisitionService(self.executor)

    def test_continuous_acquisition_short_burst(self) -> None:
        """
        Short burst acquisition:
        - sample_rate = 20 Hz
        - duration ~0.1 s
        Expect a small number of samples (> 0).
        """

        config = ContinuousAcquisitionConfig(
            sample_rate_hz=20.0,
            max_duration_s=0.1,
            target_uncertainty=None,
        )

        self.log_interaction(
            "Test",
            "CALL",
            "ContinuousAcquisitionService",
            "start_acquisition(sample_rate=20Hz, max_duration=0.1s)",
            data={"sample_rate_hz": config.sample_rate_hz, "max_duration_s": config.max_duration_s},
        )
        self.service.start_acquisition(config)

        # Wait slightly longer than max_duration to ensure worker finishes
        time.sleep(0.2)

        self.log_interaction(
            "Test",
            "CALL",
            "ContinuousAcquisitionService",
            "stop_acquisition()",
        )
        self.service.stop_acquisition()

        # Assertions
        nb_samples = len(self.samples)
        self.log_interaction(
            "Test",
            "ASSERT",
            "ContinuousAcquisitionService",
            "Verify that at least 1 sample was acquired",
            expect=">=1",
            got=nb_samples,
        )
        assert nb_samples >= 1


if __name__ == "__main__":
    import unittest

    unittest.main()


