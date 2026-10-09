import threading
import unittest
from typing import List

from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.scan_application_service.dtos.scan_dtos import Scan2DConfigDTO
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.scan_closure_handler.scan_closure_handler import ScanClosureHandler
from domain.scan.value_objects.expected_source.expected_source import ExpectedSource
from domain.scan.value_objects.scan_id.scan_id import ScanId
from domain.scan.value_objects.scan_state.scan_state import ScanState
from domain.shared_kernel.events.domain_event import DomainEvent
from domain.step_scan.events.scan_started.scan_started import ScanStarted
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.unit_of_work.in_memory_unit_of_work import InMemoryUnitOfWork


def _dto(nx=2, ny=2) -> Scan2DConfigDTO:
    return Scan2DConfigDTO(
        x_min=0, x_max=1, x_nb_points=nx,
        y_min=0, y_max=1, y_nb_points=ny,
        scan_pattern="RASTER", stabilization_delay_ms=0,
        averaging_per_position=1, uncertainty_volts=1e-6,
    )


class TestScanThinScanFlow(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.uow = InMemoryUnitOfWork(self.event_bus)
        ScanClosureHandler(self.event_bus, self.uow, ("aefipointacquired",))
        self.events: List[DomainEvent] = []
        for topic in ("scanstarted", "scanpointacquired", "scancompleted", "scanfailed"):
            self.event_bus.subscribe(topic, self.events.append)
        self.streams_running_at_completion: List[bool] = []
        self.aefi_acquisition_service = AefiAcquisitionService(
            MockAefiAcquisitionExecutor(self.event_bus), MockAcquisitionPort()
        )
        self.event_bus.subscribe(
            "scancompleted",
            lambda e: self.streams_running_at_completion.append(self.aefi_acquisition_service.is_acquisition_running()),
        )
        self.service = ScanApplicationService(
            MockMotionPort(event_bus=self.event_bus, motion_delay_ms=1),
            self.aefi_acquisition_service,
            self.event_bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=EventBusMotionSynchronizer(self.event_bus),
            unit_of_work=self.uow,
        )

    def _wait_terminal(self, timeout=10.0):
        done = threading.Event()
        self.event_bus.subscribe("scancompleted", lambda e: done.set())
        self.event_bus.subscribe("scanfailed", lambda e: done.set())
        if any(type(e).__name__ in ("ScanCompleted", "ScanFailed") for e in self.events):
            return True
        return done.wait(timeout)

    def test_starting_a_step_scan_creates_a_thin_scan_with_the_step_scan_id(self):
        self.assertTrue(self.service.execute_scan(_dto()))
        self._wait_terminal()
        started = next(e for e in self.events if isinstance(e, ScanStarted))
        with self.uow as uow:
            scan = uow.scans.get(ScanId(started.scan_id))
        self.assertIsNotNone(scan)
        self.assertEqual(scan.expected_sources, {"aefi_point": ExpectedSource(4)})
        self.assertEqual(scan.total_points, 4)
        self.assertIn(scan.state, (ScanState.STARTED, ScanState.COMPLETED))

    def test_step_scan_completes_the_thin_scan_with_a_single_scan_completed_after_all_points(self):
        self.assertTrue(self.service.execute_scan(_dto()))
        self.assertTrue(self._wait_terminal())
        started = next(e for e in self.events if isinstance(e, ScanStarted))

        names = [type(e).__name__ for e in self.events]
        self.assertEqual(names.count("ScanCompleted"), 1)
        self.assertEqual(names.count("ScanPointAcquired"), 4)
        self.assertLess(len(names) - 1 - names[::-1].index("ScanPointAcquired"), names.index("ScanCompleted"))
        with self.uow as uow:
            scan = uow.scans.get(ScanId(started.scan_id))
        self.assertEqual(scan.state, ScanState.COMPLETED)
        self.assertEqual(len(scan.received("aefi_point")), 4)

    def test_streams_are_released_before_scan_completed(self):
        self.assertTrue(self.service.execute_scan(_dto()))
        self.assertTrue(self._wait_terminal())
        self.assertEqual(self.streams_running_at_completion, [False])

    def test_thin_scan_not_found_turns_into_scan_failed(self):
        real_get = self.uow.scans.get
        calls = []

        def get_once(scan_id):  # the start finds it, the closure does not
            calls.append(scan_id)
            return real_get(scan_id) if len(calls) == 1 else None

        self.uow.scans.get = get_once
        self.assertTrue(self.service.execute_scan(_dto()))
        self.assertTrue(self._wait_terminal())

        names = [type(e).__name__ for e in self.events]
        self.assertEqual(names.count("ScanFailed"), 1)
        self.assertEqual(names.count("ScanCompleted"), 0)
        self.assertEqual(names.count("ScanPointAcquired"), 1)  # loop stops after the failure
        self.assertEqual(self.service._current_scan.status.name, "FAILED")

    def test_closure_failure_on_the_last_point_turns_into_scan_failed_not_completed(self):
        real_get = self.uow.scans.get
        calls = []

        def get_unless_last(scan_id):  # start + 3 closures succeed, the 4th point's closure does not
            calls.append(scan_id)
            return real_get(scan_id) if len(calls) < 5 else None

        self.uow.scans.get = get_unless_last
        self.assertTrue(self.service.execute_scan(_dto()))
        self.assertTrue(self._wait_terminal())

        names = [type(e).__name__ for e in self.events]
        self.assertEqual(names.count("ScanFailed"), 1)
        self.assertEqual(names.count("ScanCompleted"), 0)
        self.assertEqual(names.count("ScanPointAcquired"), 4)
        self.assertEqual(self.service._current_scan.status.name, "FAILED")


if __name__ == "__main__":
    unittest.main()
