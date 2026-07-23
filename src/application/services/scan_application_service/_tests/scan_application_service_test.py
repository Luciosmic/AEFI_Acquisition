import threading
import unittest
from datetime import datetime
from typing import List
from uuid import uuid4
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.dtos.scan_dtos import Scan2DConfigDTO
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.step_scan.events.scan_started.scan_started import ScanStarted
from domain.step_scan.events.scan_point_acquired.scan_point_acquired import ScanPointAcquired
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from domain.step_scan.events.scan_failed.scan_failed import ScanFailed
from domain.step_scan.events.electric_field_scan_point_acquired.electric_field_scan_point_acquired import ElectricFieldScanPointAcquired
from domain.electric_field_probe.value_objects.field_measurement.field_measurement import FieldMeasurement
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from tool.diagram_friendly_test import DiagramFriendlyTest

class TestScanApplicationService(DiagramFriendlyTest):
    def setUp(self):
        super().setUp()
        self.log_interaction("Test", "CREATE", "ScanApplicationService", "Setup service and ports")

        self.event_bus = InMemoryEventBus()
        self.motion_port = MockMotionPort(event_bus=self.event_bus, motion_delay_ms=10)
        self.acquisition_port = MockAcquisitionPort()
        self.events: List[DomainEvent] = []

        self.log_interaction("Test", "SUBSCRIBE", "EventBus", "Subscribe to scan events")
        self.event_bus.subscribe('scanstarted', self.on_event)
        self.event_bus.subscribe('scanpointacquired', self.on_event)
        self.event_bus.subscribe('scancompleted', self.on_event)

        task_runner = ThreadPoolTaskRunner()
        motion_sync = EventBusMotionSynchronizer(self.event_bus)

        self.service = ScanApplicationService(
            self.motion_port,
            self.acquisition_port,
            self.event_bus,
            task_runner=task_runner,
            motion_sync=motion_sync,
        )

    def on_event(self, event: DomainEvent):
        event_name = type(event).__name__
        data = {"event": event_name}

        if isinstance(event, ScanStarted):
            data["scan_id"] = str(event.scan_id)
            data["pattern"] = event.config.scan_pattern.name

        elif isinstance(event, ScanPointAcquired):
            data["point_index"] = event.point_index
            data["position"] = {"x": event.position.x, "y": event.position.y}
            data["measurement"] = {
                "x_in_phase": event.measurement.voltage_x_in_phase,
                "x_quad": event.measurement.voltage_x_quadrature
            }

        elif isinstance(event, ScanCompleted):
            data["scan_id"] = str(event.scan_id)
            data["total_points"] = event.total_points

        self.log_interaction("EventBus", "RECEIVE", "Test", f"Received {event_name}", data)
        self.events.append(event)

    def _wait_for_scan_completion(self, timeout: float = 5.0) -> bool:
        """Wait until ScanCompleted is received or timeout expires."""
        deadline = threading.Event()
        def _on_completed(event):
            deadline.set()
        self.event_bus.subscribe('scancompleted', _on_completed)
        if any(isinstance(e, ScanCompleted) for e in self.events):
            return True
        return deadline.wait(timeout=timeout)

    def test_full_scan_execution(self):
        self.log_interaction("Test", "START", "ScanApplicationService", "Start full scan execution test")

        scan_dto = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=2,
            y_min=0, y_max=1, y_nb_points=2,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=1,
            uncertainty_volts=1e-6
        )
        self.log_interaction("Test", "CREATE", "Scan2DConfigDTO", "Create scan config", {"pattern": scan_dto.scan_pattern})

        self.log_interaction("Test", "COMMAND", "ScanApplicationService", "Execute scan")
        success = self.service.execute_scan(scan_dto)

        self.log_interaction("Test", "ASSERT", "ScanApplicationService", "Verify execution success", expect=True, got=success)
        self.assertTrue(success)

        completed = self._wait_for_scan_completion(timeout=5.0)
        self.assertTrue(completed, "Scan did not complete within timeout")

        self.log_interaction("Test", "ASSERT", "EventBus", "Verify ScanStarted event")
        self.assertTrue(any(isinstance(e, ScanStarted) for e in self.events))

        self.log_interaction("Test", "ASSERT", "EventBus", "Verify ScanCompleted event")
        self.assertTrue(any(isinstance(e, ScanCompleted) for e in self.events))

        points_acquired = [e for e in self.events if isinstance(e, ScanPointAcquired)]
        self.log_interaction("Test", "ASSERT", "EventBus", "Verify points acquired", expect=4, got=len(points_acquired))
        self.assertEqual(len(points_acquired), 4)

        self.log_interaction("Test", "ASSERT", "MotionPort", "Verify move history", expect=4, got=len(self.motion_port.move_history))
        self.assertEqual(len(self.motion_port.move_history), 4)

    def test_subscriptions(self):
        """Test the subscription methods."""
        self.log_interaction("Test", "START", "ScanApplicationService", "Start subscription test")

        received_updates = []
        received_completion = []
        done = threading.Event()

        def on_update(event):
            received_updates.append(event)

        def on_completion(event):
            received_completion.append(event)
            done.set()

        self.log_interaction("Test", "CALL", "ScanApplicationService", "Subscribe to updates")
        self.service.subscribe_to_scan_updates(on_update)

        self.log_interaction("Test", "CALL", "ScanApplicationService", "Subscribe to completion")
        self.service.subscribe_to_scan_completion(on_completion)

        scan_dto = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=2,
            y_min=0, y_max=1, y_nb_points=2,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=1,
            uncertainty_volts=1e-6
        )
        self.service.execute_scan(scan_dto)

        self.assertTrue(done.wait(timeout=5.0), "Scan did not complete within timeout")

        self.log_interaction("Test", "ASSERT", "ScanApplicationService", "Verify updates received", expect=4, got=len(received_updates))
        self.assertEqual(len(received_updates), 4)

        self.log_interaction("Test", "ASSERT", "ScanApplicationService", "Verify completion received", expect=1, got=len(received_completion))
        self.assertEqual(len(received_completion), 1)

    def test_electric_field_scan_point_forwarded_to_output_port(self):
        """ElectricFieldScanPointAcquired must be flattened (component_N + norm) and forwarded."""
        received = []
        self.service.set_output_port(_RecordingOutputPort(received))

        event = ElectricFieldScanPointAcquired(
            scan_id=uuid4(),
            point_index=3,
            position=Position2D(x=1.0, y=2.0),
            field_measurement=FieldMeasurement(components=(3.0, 4.0), timestamp=datetime.now()),
        )
        self.event_bus.publish("electricfieldscanpointacquired", event)

        self.assertEqual(len(received), 1)
        current, total, data = received[0]
        self.assertEqual(current, 3)
        self.assertEqual(data["x"], 1.0)
        self.assertEqual(data["y"], 2.0)
        self.assertEqual(data["value"], {"component_0": 3.0, "component_1": 4.0, "norm": 5.0})

    def test_field_probe_point_retried_until_complete(self):
        """A point stays unvalidated across a bad sampling pass and is only
        confirmed once the full averaging window is actually collected."""
        # First FIELD_SAMPLE_MAX_RETRIES+1 calls fail (exhausts one sample's
        # retry budget, forcing an extra point-level pass), then it recovers.
        probe = _ScriptedFieldProbePort(script=[False, False, False, True])
        service = ScanApplicationService(
            self.motion_port, self.acquisition_port, self.event_bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=EventBusMotionSynchronizer(self.event_bus),
            field_probe_port=probe,
        )
        self.event_bus.subscribe('scanpointacquired', self.on_event)
        self.event_bus.subscribe('scancompleted', self.on_event)

        scan_dto = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=1,
            y_min=0, y_max=1, y_nb_points=1,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=1,
            uncertainty_volts=1e-6,
        )
        self.assertTrue(service.execute_scan(scan_dto))

        deadline = threading.Event()
        self.event_bus.subscribe('scancompleted', lambda e: deadline.set())
        self.assertTrue(deadline.wait(timeout=5.0), "Scan did not complete within timeout")

        self.assertTrue(any(isinstance(e, ScanCompleted) for e in self.events))
        self.assertTrue(any(isinstance(e, ScanPointAcquired) for e in self.events))

    def test_field_probe_exhausted_retry_budget_fails_scan(self):
        """If the probe never recovers within the point-level retry budget,
        the scan fails instead of validating an incomplete point."""
        probe = _ScriptedFieldProbePort(script=[False])  # always fails
        service = ScanApplicationService(
            self.motion_port, self.acquisition_port, self.event_bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=EventBusMotionSynchronizer(self.event_bus),
            field_probe_port=probe,
        )
        self.event_bus.subscribe('scanpointacquired', self.on_event)
        self.event_bus.subscribe('scanfailed', self.on_event)

        scan_dto = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=1,
            y_min=0, y_max=1, y_nb_points=1,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=1,
            uncertainty_volts=1e-6,
        )
        self.assertTrue(service.execute_scan(scan_dto))

        deadline = threading.Event()
        self.event_bus.subscribe('scanfailed', lambda e: deadline.set())
        self.assertTrue(deadline.wait(timeout=5.0), "Scan did not fail within timeout")

        self.assertTrue(any(isinstance(e, ScanFailed) for e in self.events))
        self.assertFalse(any(isinstance(e, ScanPointAcquired) for e in self.events))


class _ScriptedFieldProbePort:
    """Minimal IElectricFieldProbePort fake — acquire_sample() follows a
    scripted pass/fail sequence (cycled), to drive point-level retry paths."""

    def __init__(self, script: List[bool]):
        self._script = script
        self._call_count = 0

    def is_ready(self) -> bool:
        return True

    def acquire_sample(self) -> FieldMeasurement:
        outcome = self._script[self._call_count % len(self._script)]
        self._call_count += 1
        if not outcome:
            raise RuntimeError("simulated Narda comm failure")
        return FieldMeasurement(components=(1.0, 2.0, 3.0), timestamp=datetime.now())

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def is_connected(self) -> bool:
        return True

    def get_probe(self):
        return None


class _RecordingOutputPort:
    """Minimal IScanOutputPort fake — records present_field_scan_progress calls only."""

    def __init__(self, sink: List):
        self._sink = sink

    def present_field_scan_progress(self, current_point_index, total_points, point_data):
        self._sink.append((current_point_index, total_points, point_data))

    def __getattr__(self, name):
        return lambda *a, **k: None


if __name__ == '__main__':
    unittest.main()
