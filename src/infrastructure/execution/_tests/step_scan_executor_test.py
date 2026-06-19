import threading
import unittest
from unittest.mock import MagicMock

from tool.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.step_scan_executor import StepScanExecutor
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from domain.aggregates.step_scan import StepScan
from domain.value_objects.scan.scan_trajectory import ScanTrajectory
from domain.value_objects.scan.step_scan_config import StepScanConfig, ScanPattern
from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.acquisition.acquisition_sample import AcquisitionSample


class TracingAcquisitionPort:
    """Logs acquire_sample calls; returns a fixed sample (no event bus needed)."""
    def __init__(self, test_case: DiagramFriendlyTest):
        self._test = test_case
        self.mock = MagicMock()
        self.mock.acquire_sample.return_value = AcquisitionSample(
            voltage_x_in_phase=1.0, voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0, voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0, voltage_z_quadrature=0.0,
            timestamp=0.0,
        )

    def acquire_sample(self):
        self._test.log_interaction("StepScanExecutor", "CALL", "AcquisitionPort", "Call acquire_sample")
        result = self.mock.acquire_sample()
        self._test.log_interaction("AcquisitionPort", "RETURN", "StepScanExecutor", "Return from acquire_sample")
        return result

    def is_ready(self):
        return True

    def get_quantification_noise(self):
        return 0.0


class TestStepScanExecutor(DiagramFriendlyTest):
    def setUp(self):
        super().setUp()

        # Real event bus so event subscriptions actually route callbacks
        self.event_bus = InMemoryEventBus()
        self._publish_count = 0
        _original_publish = self.event_bus.publish

        def _tracking_publish(topic, event):
            self._publish_count += 1
            self.log_interaction("StepScanExecutor", "CALL", "EventBus", f"Call publish ({topic})")
            _original_publish(topic, event)

        self.event_bus.publish = _tracking_publish

        # Real MockMotionPort wired to the same bus so MotionCompleted events arrive
        self.motion_port = MockMotionPort(event_bus=self.event_bus, motion_delay_ms=10)

        # Tracing acquisition port (no event bus needed)
        self.acquisition_port = TracingAcquisitionPort(self)

        self.log_interaction("Test", "CREATE", "StepScanExecutor", "Initialize Executor")
        self.executor = StepScanExecutor(
            motion_port=self.motion_port,
            acquisition_port=self.acquisition_port,
            event_bus=self.event_bus,
        )

    def test_execute_nominal_case(self):
        self.log_interaction("Test", "START", "StepScanExecutor", "Start nominal execution test")

        from domain.value_objects.scan.scan_zone import ScanZone
        from domain.value_objects.measurement_uncertainty import MeasurementUncertainty

        scan_zone = ScanZone(x_min=0, x_max=1, y_min=0, y_max=1)
        uncertainty = MeasurementUncertainty(max_uncertainty_volts=1e-6)

        config = StepScanConfig(
            scan_zone=scan_zone,
            x_nb_points=2,
            y_nb_points=1,
            scan_pattern=ScanPattern.RASTER,
            stabilization_delay_ms=0,
            averaging_per_position=1,
            measurement_uncertainty=uncertainty,
        )
        trajectory = ScanTrajectory([Position2D(0, 0), Position2D(1, 0)])
        scan = StepScan()
        scan.start(config)

        # Subscribe before executing so we catch ScanCompleted
        done = threading.Event()
        self.event_bus.subscribe("scancompleted", lambda e: done.set())

        self.log_interaction("Test", "CALL", "StepScanExecutor", "execute")
        success = self.executor.execute(scan, trajectory, config)

        self.log_interaction("Test", "ASSERT", "StepScanExecutor", "Check success", expect="True", got=str(success))
        self.assertTrue(success)

        # Wait for worker thread to finish (2 points × 10 ms + buffer)
        self.assertTrue(done.wait(timeout=5.0), "Scan did not complete within timeout")

        self.log_interaction("Test", "ASSERT", "EventBus", "Check publish calls")
        # ScanStarted + 2×ScanPointAcquired + ScanCompleted = 4 minimum
        self.assertTrue(self._publish_count >= 4, f"Expected >= 4 publishes, got {self._publish_count}")


if __name__ == '__main__':
    unittest.main()
