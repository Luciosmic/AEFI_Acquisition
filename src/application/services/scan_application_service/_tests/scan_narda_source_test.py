"""Le canal Narda commite un NardaPoint et le Scan le declare comme source requise."""

import threading
import unittest
from datetime import datetime
from typing import List

from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.electric_field_probe_service.electric_field_probe_service import ElectricFieldProbeService
from application.services.scan_application_service.dtos.scan_dtos import Scan2DConfigDTO
from application.services.scan_application_service.scan_application_service import (
    ScanApplicationService,
    make_electric_field_probe_channel,
)
from application.services.scan_application_service.scan_closure_handler.scan_closure_handler import ScanClosureHandler
from domain.electric_field_probe.value_objects.field_measurement.field_measurement import FieldMeasurement
from domain.narda_point.events.narda_point_acquired.narda_point_acquired import NardaPointAcquired
from domain.scan.value_objects.expected_source.expected_source import ExpectedSource
from domain.scan.value_objects.scan_id.scan_id import ScanId
from domain.scan.value_objects.scan_state.scan_state import ScanState
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.step_scan.events.scan_failed.scan_failed import ScanFailed
from domain.step_scan.events.scan_started.scan_started import ScanStarted
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.electric_field_probe_acquisition_executor import (
    ElectricFieldProbeAcquisitionExecutor,
)
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.unit_of_work.in_memory_unit_of_work import InMemoryUnitOfWork


class _FieldProbePort:
    """Minimal IElectricFieldProbePort: always samples, readiness is switchable."""

    def __init__(self, ready: bool = True):
        self.ready = ready

    def is_ready(self) -> bool:
        return self.ready

    def acquire_sample(self) -> FieldMeasurement:
        return FieldMeasurement(components=(1.0, 2.0, 3.0), timestamp=datetime.now())

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def is_connected(self) -> bool:
        return True

    def get_probe(self):
        return None


def _dto() -> Scan2DConfigDTO:
    return Scan2DConfigDTO(
        x_min=0, x_max=1, x_nb_points=2,
        y_min=0, y_max=1, y_nb_points=2,
        scan_pattern="RASTER", stabilization_delay_ms=0,
        averaging_per_position=1, uncertainty_volts=1e-6,
    )


class TestScanNardaSource(unittest.TestCase):
    def setUp(self):
        self.bus = InMemoryEventBus()
        self.uow = InMemoryUnitOfWork(self.bus)
        ScanClosureHandler(self.bus, self.uow, ("aefipointacquired", "nardapointacquired"))
        self.events: List[DomainEvent] = []
        for topic in ("scanstarted", "scanpointacquired", "scancompleted", "scanfailed",
                      "nardapointacquired", "aefipointacquired"):
            self.bus.subscribe(topic, self.events.append)
        self.terminal = threading.Event()
        self.bus.subscribe("scancompleted", lambda e: self.terminal.set())
        self.bus.subscribe("scanfailed", lambda e: self.terminal.set())

    def _service(self, probe: _FieldProbePort) -> ScanApplicationService:
        field_service = ElectricFieldProbeService(
            executor=ElectricFieldProbeAcquisitionExecutor(self.bus), probe_port=probe, event_bus=self.bus
        )
        channel = make_electric_field_probe_channel(
            probe_port=probe, probe_service=field_service, event_bus=self.bus, unit_of_work=self.uow
        )
        service = ScanApplicationService(
            MockMotionPort(event_bus=self.bus, motion_delay_ms=1),
            AefiAcquisitionService(MockAefiAcquisitionExecutor(self.bus), MockAcquisitionPort()),
            self.bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=EventBusMotionSynchronizer(self.bus),
            auxiliary_probes=[channel],
            unit_of_work=self.uow,
        )
        service.POINT_ACQUISITION_TIMEOUT_S = 2.0
        return service

    def _thin_scan(self):
        started = next(e for e in self.events if isinstance(e, ScanStarted))
        with self.uow as uow:
            return uow.scans.get(ScanId(started.scan_id)), started.scan_id

    def _of_type(self, cls):
        return [e for e in self.events if isinstance(e, cls)]

    def test_ready_probe_is_a_required_source_and_scan_completes_with_both_sources(self):
        self.assertTrue(self._service(_FieldProbePort()).execute_scan(_dto()))
        self.assertTrue(self.terminal.wait(10.0))

        scan, scan_id = self._thin_scan()
        self.assertEqual(
            scan.expected_sources,
            {"aefi_point": ExpectedSource(4), "narda_point": ExpectedSource(4, required=True)},
        )
        self.assertEqual(scan.state, ScanState.COMPLETED)
        self.assertEqual(len(scan.received("narda_point")), 4)
        with self.uow as uow:
            self.assertEqual(len(uow.narda_points.list_by_scan(scan_id)), 4)

    def test_narda_event_of_a_point_is_published_after_commit_and_before_the_aefi_point(self):
        self.assertTrue(self._service(_FieldProbePort()).execute_scan(_dto()))
        self.assertTrue(self.terminal.wait(10.0))

        names = [type(e).__name__ for e in self.events
                 if type(e).__name__ in ("NardaPointAcquired", "AefiPointAcquired")]
        self.assertEqual(names, ["NardaPointAcquired", "AefiPointAcquired"] * 4)
        narda = self._of_type(NardaPointAcquired)
        self.assertEqual([e.point_index for e in narda], [0, 1, 2, 3])

    def test_probe_not_ready_at_start_leaves_the_source_undeclared(self):
        self.assertTrue(self._service(_FieldProbePort(ready=False)).execute_scan(_dto()))
        self.assertTrue(self.terminal.wait(10.0))

        scan, scan_id = self._thin_scan()
        self.assertEqual(scan.expected_sources, {"aefi_point": ExpectedSource(4)})
        self.assertEqual(scan.state, ScanState.COMPLETED)
        self.assertEqual(self._of_type(NardaPointAcquired), [])

    def test_probe_lost_mid_scan_fails_the_scan_with_an_explicit_reason(self):
        probe = _FieldProbePort()
        service = self._service(probe)

        def _lose_probe(_event):
            probe.ready = False

        self.bus.subscribe("scanpointacquired", _lose_probe)
        self.assertTrue(service.execute_scan(_dto()))
        self.assertTrue(self.terminal.wait(10.0))

        failed = self._of_type(ScanFailed)
        self.assertEqual(len(failed), 1)
        self.assertIn("became unavailable", failed[0].reason)
        self.assertIn("narda_point", failed[0].reason)
        scan, _ = self._thin_scan()
        self.assertEqual(scan.state, ScanState.STARTED)


if __name__ == "__main__":
    unittest.main()
