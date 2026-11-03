"""get_status / pause_scan / resume_scan / cancel_scan on a running step-scan (mock stack)."""
import threading
import time
import unittest
from typing import List

from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.scan_application_service.dtos.scan_dtos import Scan2DConfigDTO
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.scan_closure_handler.scan_closure_handler import ScanClosureHandler
from domain.shared_kernel.events.domain_event import DomainEvent
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.unit_of_work.in_memory_unit_of_work import InMemoryUnitOfWork


def _dto() -> Scan2DConfigDTO:
    return Scan2DConfigDTO(
        x_min=0, x_max=1, x_nb_points=2,
        y_min=0, y_max=1, y_nb_points=2,
        scan_pattern="RASTER", stabilization_delay_ms=0,
        averaging_per_position=1, uncertainty_volts=1e-6,
    )


class TestScanControlCommands(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        uow = InMemoryUnitOfWork(self.event_bus)
        ScanClosureHandler(self.event_bus, uow, ("aefipointacquired",))
        self.aefi = AefiAcquisitionService(MockAefiAcquisitionExecutor(self.event_bus), MockAcquisitionPort())
        self.service = ScanApplicationService(
            MockMotionPort(event_bus=self.event_bus, motion_delay_ms=5),
            self.aefi,
            self.event_bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=EventBusMotionSynchronizer(self.event_bus),
            unit_of_work=uow,
        )
        self.events: List[DomainEvent] = []
        self.flags = {name: threading.Event() for name in ("scanpaused", "scanresumed", "scancompleted", "scancancelled")}
        for name, flag in self.flags.items():
            self.event_bus.subscribe(name, lambda e, f=flag: (self.events.append(e), f.set()))

    def _names(self) -> List[str]:
        return [type(e).__name__ for e in self.events]

    def test_status_before_any_scan_is_pending_and_empty(self):
        status = self.service.get_status()
        self.assertEqual((status.status, status.current_point_index, status.total_points), ("pending", 0, 0))
        self.assertFalse(status.is_running)

    def test_pause_resume_cancel_without_a_scan_do_nothing(self):
        self.service.pause_scan()
        self.service.resume_scan()
        self.service.cancel_scan()
        self.assertEqual(self.events, [])

    def test_status_reports_the_index_and_total_while_running_then_completed(self):
        seen = []
        self.event_bus.subscribe("scanpointacquired", lambda e: seen.append(self.service.get_status()))

        self.assertTrue(self.service.execute_scan(_dto()))
        self.assertTrue(self.flags["scancompleted"].wait(10.0))

        self.assertEqual([s.current_point_index for s in seen], [1, 2, 3, 4])
        self.assertTrue(all(s.total_points == 4 for s in seen))
        self.assertTrue(all(s.is_running for s in seen[:3]))  # the last one may already be closing
        self.assertAlmostEqual(seen[1].progress_percentage, 50.0)
        final = self.service.get_status()
        self.assertEqual((final.status, final.current_point_index, final.total_points), ("completed", 4, 4))
        self.assertAlmostEqual(final.progress_percentage, 100.0)

    def test_pause_after_the_last_point_is_ignored(self):
        self.assertTrue(self.service.execute_scan(_dto()))
        self.assertTrue(self.flags["scancompleted"].wait(10.0))

        self.service.pause_scan()

        self.assertFalse(self.flags["scanpaused"].is_set())
        self.assertEqual(self.service.get_status().status, "completed")

    def test_pause_then_resume_continues_to_completion(self):
        first = threading.Event()

        def pause_once(event):
            if not first.is_set():
                first.set()
                self.service.pause_scan()

        self.event_bus.subscribe("scanpointacquired", pause_once)

        self.assertTrue(self.service.execute_scan(_dto()))
        self.assertTrue(self.flags["scanpaused"].wait(10.0))
        status = self.service.get_status()
        self.assertTrue(status.is_paused)
        self.assertEqual(status.current_point_index, 1)
        paused = next(e for e in self.events if type(e).__name__ == "ScanPaused")
        self.assertEqual(paused.current_point_index, 1)

        self.service.resume_scan()
        self.assertTrue(self.flags["scancompleted"].wait(10.0))

        resumed = next(e for e in self.events if type(e).__name__ == "ScanResumed")
        self.assertEqual(resumed.resume_from_point_index, 1)
        self.assertEqual(self.service.get_status().current_point_index, 4)

    def test_cancel_stops_the_loop_and_releases_the_stream(self):
        first = threading.Event()

        def cancel_once(event):
            if not first.is_set():
                first.set()
                self.service.cancel_scan()

        self.event_bus.subscribe("scanpointacquired", cancel_once)

        self.assertTrue(self.service.execute_scan(_dto()))
        self.assertTrue(self.flags["scancancelled"].wait(10.0))
        deadline = time.monotonic() + 5.0
        while self.aefi.is_acquisition_running() and time.monotonic() < deadline:
            time.sleep(0.05)

        self.assertEqual(self.service.get_status().status, "cancelled")
        self.assertFalse(self.aefi.is_acquisition_running())
        self.assertNotIn("ScanCompleted", self._names())
        self.assertLess(self.service.get_status().current_point_index, 4)

    def test_cancel_in_the_window_after_the_last_point_is_ignored(self):
        def cancel_on_last(event):
            if self.service.get_status().current_point_index == self.service.get_status().total_points:
                self.service.cancel_scan()

        self.event_bus.subscribe("scanpointacquired", cancel_on_last)

        self.assertTrue(self.service.execute_scan(_dto()))
        self.assertTrue(self.flags["scancompleted"].wait(10.0))
        deadline = time.monotonic() + 5.0
        while self.aefi.is_acquisition_running() and time.monotonic() < deadline:
            time.sleep(0.05)

        self.assertNotIn("ScanCancelled", self._names())
        self.assertEqual(self._names().count("ScanCompleted"), 1)
        self.assertEqual(self.service.get_status().status, "completed")
        self.assertFalse(self.aefi.is_acquisition_running())

    def test_cancel_after_a_final_status_is_a_no_op_and_does_not_raise(self):
        self.assertTrue(self.service.execute_scan(_dto()))
        self.assertTrue(self.flags["scancompleted"].wait(10.0))
        before = len(self.events)

        self.service.cancel_scan()  # shutdown path: must not raise

        self.assertEqual(len(self.events), before)
        self.assertEqual(self.service.get_status().status, "completed")


if __name__ == "__main__":
    unittest.main()
