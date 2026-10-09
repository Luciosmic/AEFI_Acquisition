"""
Integration test: a fly scan sweeps each line of the grid in one go and
emits its grid points live, while the motor moves — on the same motion stack
as the app's mock mode (real ArcusAdapter over the bench-faithful fake
controller), no hardware.
"""
import threading
import time
import unittest

import pytest

from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.dtos.scan_dtos import Scan2DConfigDTO
from application.services.scan_application_service.scan_closure_handler.scan_closure_handler import ScanClosureHandler
from domain.scan.value_objects.scan_id.scan_id import ScanId
from domain.scan.value_objects.scan_state.scan_state import ScanState
from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from domain.step_scan.value_objects.scan_status.scan_status import ScanStatus
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.hardware.arcus_performax_4EX.fake.fake_arcus_performax4ex_controller import (
    FakeArcusPerformax4EXController,
)
from infrastructure.unit_of_work.in_memory_unit_of_work import InMemoryUnitOfWork
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort


def make_dto(**overrides):
    # 3 columns (X) of 4 points (Y, fast axis), 30 mm lines.
    params = dict(
        x_min=600.0, x_max=620.0, x_nb_points=3,
        y_min=600.0, y_max=630.0, y_nb_points=4,
        scan_pattern="SERPENTINE", scan_axis="Y",
        stabilization_delay_ms=0, averaging_per_position=1, uncertainty_volts=0.001,
        fly_scan=True,
    )
    params.update(overrides)
    return Scan2DConfigDTO(**params)


class _PreviewPort:
    """Minimal IScanOutputPort fake — records the provisional previews."""

    def __init__(self, shown, service):
        self.shown = shown

    def present_scan_line_preview(self, line_index, index_in_line, point_data):
        self.shown.append((line_index, index_in_line, point_data))

    def __getattr__(self, name):
        return lambda *a, **k: None


class _Stack(unittest.TestCase):
    def _service(self, motion_port):
        self.uow = InMemoryUnitOfWork(self.event_bus)
        ScanClosureHandler(self.event_bus, self.uow, ("aefipointacquired", "aefilineacquired"))
        self.continuous_service = AefiAcquisitionService(
            MockAefiAcquisitionExecutor(self.event_bus),
            RandomNoiseAcquisitionPort(noise_std=0.0, seed=1),
        )
        return ScanApplicationService(
            motion_port,
            self.continuous_service,
            self.event_bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=EventBusMotionSynchronizer(self.event_bus),
            unit_of_work=self.uow,
        )

    def _run(self, dto, until="scancompleted", timeout=30.0):
        # Subscribe before execute: the scan runs on a background thread.
        done = threading.Event()
        self.event_bus.subscribe(until, lambda e: done.set())
        self.assertTrue(self.service.execute_scan(dto))
        self.assertTrue(done.wait(timeout=timeout), f"No {until} within timeout")
        return self.service._current_scan

    def _lines(self, scan):
        with self.uow as uow:
            return uow.aefi_lines.list_by_scan(scan.id)


class TestFlyScanOnTheFaithfulMotionStack(_Stack):

    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.controller = FakeArcusPerformax4EXController()
        self.controller.connect()
        self.controller.home_both()
        # Start at the grid corner: travelling there from home takes ~10 s.
        for axis in ("x", "y"):
            self.controller.set_position_reference(axis, round(600.0 * 1000.0 / 21.8))
        self.adapter = ArcusAdapter(event_bus=self.event_bus)
        self.adapter.set_microns_per_pulse(21.8)
        self.adapter.set_controller(self.controller)
        self.adapter.enable()
        self.addCleanup(self.adapter.disable)
        self.adapter.set_speed_mode("fast")
        self.service = self._service(self.adapter)

        # Timeline of what the UI would see: points vs end of each motion.
        self.timeline = []
        self.event_bus.subscribe("scanpointacquired", lambda e: self.timeline.append(("point", e.point_index)))
        self.event_bus.subscribe("motioncompleted", lambda e: self.timeline.append(("motion_done", None)))

    def test_fly_scan_fills_the_grid_in_travel_order(self):
        scan = self._run(make_dto())

        self.assertEqual(scan.status, ScanStatus.COMPLETED)
        points = [p for line in self._lines(scan) for p in line.points]
        positions = [(p.position.x, p.position.y) for p in points]
        self.assertEqual(positions, pytest.approx([
            (600.0, 600.0), (600.0, 610.0), (600.0, 620.0), (600.0, 630.0),
            (610.0, 630.0), (610.0, 620.0), (610.0, 610.0), (610.0, 600.0),
            (620.0, 600.0), (620.0, 610.0), (620.0, 620.0), (620.0, 630.0),
        ]))
        self.assertEqual([p.index_in_line for p in points], [0, 1, 2, 3] * 3)

    def test_scan_completed_is_emitted_once_by_the_thin_scan_after_every_point(self):
        names = []
        for topic in ("scanpointacquired", "scancompleted", "aefilineacquired"):
            self.event_bus.subscribe(topic, lambda e: names.append(type(e).__name__))
        completed = []
        self.event_bus.subscribe("scancompleted", completed.append)

        scan = self._run(make_dto())

        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].total_points, 12)
        self.assertEqual(names.count("ScanPointAcquired"), 12)
        self.assertEqual(names.count("AefiLineAcquired"), 3)
        self.assertGreater(names.index("ScanCompleted"), len(names) - 1 - names[::-1].index("ScanPointAcquired"))
        with self.uow as uow:
            thin = uow.scans.get(ScanId(scan.id))
        self.assertEqual(thin.state, ScanState.COMPLETED)

    def test_points_of_a_line_are_published_only_once_the_line_is_complete(self):
        completed = []
        self.event_bus.subscribe("scancompleted", completed.append)
        scan = self._run(make_dto())

        # Per line: 4 ScanPointAcquired, all after the sweep's motion end — none during
        # a sweep (AefiLine is atomic, nothing of an uncommitted line reaches the export).
        done = [i for i, (kind, _) in enumerate(self.timeline) if kind == "motion_done"]
        points = [i for i, (kind, _) in enumerate(self.timeline) if kind == "point"]
        self.assertEqual(len(points), 12)
        # moves alternate start/sweep: the sweep ends are motion_done #2, #4, #6 (1-based)
        for line in range(3):
            sweep_end = done[2 * line + 1]
            line_points = points[4 * line:4 * line + 4]
            self.assertTrue(all(i > sweep_end for i in line_points), self.timeline)
            if line < 2:
                self.assertTrue(all(i < done[2 * line + 2] for i in line_points), self.timeline)
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].total_points, 12)
        self.assertEqual(self.service.get_status().current_point_index, 12)

    def test_a_provisional_preview_is_published_during_the_sweep_and_counts_for_nothing(self):
        kinds = []
        self.event_bus.subscribe("aefilinepreviewpointacquired", lambda e: kinds.append(("preview", e.line_index, e.index_in_line)))
        self.event_bus.subscribe("aefilineacquired", lambda e: kinds.append(("commit", e.line_index, None)))
        self.event_bus.subscribe("scanpointacquired", lambda e: kinds.append(("point", None, None)))
        shown = []
        port = _PreviewPort(shown, self.service)
        self.service.set_output_port(port)

        self._run(make_dto())

        # Per line, every preview of the line precedes its commit; the definitive points
        # follow the previews of the same line.
        for line in range(3):
            commit = kinds.index(("commit", line, None))
            previews = [i for i, k in enumerate(kinds) if k[0] == "preview" and k[1] == line]
            self.assertEqual(len(previews), 4)
            self.assertTrue(all(i < commit for i in previews), kinds)
        self.assertEqual(len(shown), 12)
        # The progress (definitive) count only moves with ScanPointAcquired: 12, not 24.
        self.assertEqual(self.service.get_status().current_point_index, 12)
        self.assertEqual(sum(1 for k in kinds if k[0] == "point"), 12)

    def test_fly_scan_releases_the_adc_stream_it_started(self):
        self._run(make_dto())

        self.assertFalse(self.continuous_service.is_acquisition_running())
        self.assertIsNone(self.continuous_service.get_controller())  # held during the scan only


class TestFlyScanFailureModes(_Stack):

    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.service = self._service(MockMotionPort(event_bus=self.event_bus, motion_delay_ms=100))

    def test_fly_scan_fails_when_a_line_yields_no_samples(self):
        # ADC stream already "running" elsewhere but silent: the scan neither
        # starts it nor receives anything.
        self.continuous_service.is_acquisition_running = lambda: True

        scan = self._run(make_dto(), until="scanfailed")

        self.assertEqual(scan.status, ScanStatus.FAILED)
        self.assertEqual(self._lines(scan), [])

    def test_fly_scan_rejects_differential_mode(self):
        self.assertFalse(self.service.execute_scan(make_dto(differential_mode=True)))
        self.assertIsNone(self.service._current_scan)


if __name__ == "__main__":
    unittest.main()
