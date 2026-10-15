"""
Integration test: a fly scan sweeps each line of the grid in one go and
emits its grid points live, while the motor moves — on the same motion stack
as the app's mock mode (real ArcusAdapter over the bench-faithful fake
controller), no hardware.
"""
import logging
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
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.acquisition_conditions.fake.fake_acquisition_conditions_port import FakeAcquisitionConditionsPort
from infrastructure.hardware.serial_link.fake.fake_usb_latency_timer_port import FakeUsbLatencyTimerPort
from infrastructure.provenance.fake.fake_software_provenance_port import FakeSoftwareProvenancePort
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
)
from application.services.scan_export_service.dtos.scan_export_dtos import ExportConfigDTO
from application.services.scan_export_service.scan_export_service import ScanExportService
from application.services.scan_application_service._tests.scan_export_closes_after_last_point_test import (
    _RecordingExportPort,
)


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
        self.abandoned_seen = []

    def present_scan_line_preview(self, line_index, index_in_line, point_data):
        self.shown.append((line_index, index_in_line, point_data))

    def present_scan_line_abandoned(self, line_index, reason):
        self.abandoned_seen.append((line_index, reason))

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

    def test_streams_are_released_once_without_unsubscribe_warnings(self):
        # Released before the last commit, then again by the loop's `finally`: the second call is a no-op.
        messages = []
        handler = logging.Handler(level=logging.WARNING)
        handler.emit = lambda record: messages.append(record.getMessage())
        logging.getLogger().addHandler(handler)
        self.addCleanup(logging.getLogger().removeHandler, handler)

        self._run(make_dto())
        time.sleep(0.3)  # the loop's `finally` runs after ScanCompleted

        self.assertEqual([m for m in messages if "Handler not found" in m], [])

    def test_fly_scan_releases_the_adc_stream_it_started(self):
        self._run(make_dto())

        self.assertFalse(self.continuous_service.is_acquisition_running())
        self.assertIsNone(self.continuous_service.get_controller())  # held during the scan only


class _FaithfulFlyStack(_Stack):

    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.controller = FakeArcusPerformax4EXController()
        self.controller.connect()
        self.controller.home_both()
        for axis in ("x", "y"):
            self.controller.set_position_reference(axis, round(600.0 * 1000.0 / 21.8))
        self.adapter = ArcusAdapter(event_bus=self.event_bus)
        self.adapter.set_microns_per_pulse(21.8)
        self.adapter.set_controller(self.controller)
        self.adapter.enable()
        self.addCleanup(self.adapter.disable)
        self.adapter.set_speed_mode("fast")
        self.stops = []
        real_stop = self.adapter.stop
        self.adapter.stop = lambda *a, **k: (self.stops.append(1), real_stop(*a, **k))[1]
        self.service = self._service(self.adapter)

        self.point_indices = []
        self.abandoned = []
        self.acquired_lines = []
        self.event_bus.subscribe("scanpointacquired", lambda e: self.point_indices.append(e.point_index))
        self.event_bus.subscribe("aefilineabandoned", self.abandoned.append)
        self.event_bus.subscribe("aefilineacquired", lambda e: self.acquired_lines.append(e.line_index))
        self.lines_when_paused = None

    def _on_first_preview_of_line(self, line_index, action):
        """On the first preview point of `line_index` (mid-sweep): run `action()`."""
        fired = []

        def on_preview(event):
            if event.line_index == line_index and not fired:
                fired.append(True)
                action()

        self.event_bus.subscribe("aefilinepreviewpointacquired", on_preview)

    def _committed_lines(self, scan):
        return [l.line_index for l in self._lines(scan)]


class TestFlyScanPauseRollsBackTheCurrentLine(_FaithfulFlyStack):
    """A pause inside a line abandons it (AefiLine is atomic) and the line is redone from its start."""

    def _pause_in_line_1(self, then):
        def action():
            self.service.pause_scan()
            self.lines_when_paused = self._committed_lines(self.service._current_scan)
            then()

        self._on_first_preview_of_line(1, action)

    def _assert_whole_grid_once(self, scan):
        self.assertEqual(scan.status, ScanStatus.COMPLETED)
        self.assertEqual(sorted(self.point_indices), list(range(12)))  # no duplicate, no partial point
        self.assertEqual(self.acquired_lines, [0, 1, 2])  # one AefiLineAcquired per line
        points = [p for line in self._lines(scan) for p in line.points]
        self.assertEqual([p.index_in_line for p in points], [0, 1, 2, 3] * 3)
        self.assertEqual(len(points), 12)

    def test_pause_mid_line_abandons_the_line_then_redoes_it_from_its_start(self):
        completed = []
        self.event_bus.subscribe("scancompleted", completed.append)
        port = _PreviewPort([], self.service)
        self.service.set_output_port(port)
        self._pause_in_line_1(lambda: threading.Timer(0.5, self.service.resume_scan).start())

        scan = self._run(make_dto(), timeout=90.0)

        self.assertEqual(port.abandoned_seen, [(1, "paused")])  # routed to the output port
        self.assertEqual(self.lines_when_paused, [0])  # no AefiLine for line 1 while it is partial
        self._assert_whole_grid_once(scan)
        self.assertEqual([(a.line_index, a.reason) for a in self.abandoned], [(1, "paused")])
        self.assertGreaterEqual(len(self.stops), 1)  # the motor was stopped at once
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].total_points, 12)

    def test_pause_then_resume_in_the_same_handler_still_abandons_the_line(self):
        self._pause_in_line_1(self.service.resume_scan)

        scan = self._run(make_dto(), timeout=90.0)

        self._assert_whole_grid_once(scan)
        self.assertEqual([a.line_index for a in self.abandoned], [1])

    def test_pause_while_moving_to_the_line_start_abandons_nothing_but_stops_the_motor(self):
        line_1_start = (610.0, 630.0)
        real_move_to = self.adapter.move_to
        fired = []

        def move_to(position):
            motion_id = real_move_to(position)
            if (position.x, position.y) == pytest.approx(line_1_start) and not fired:
                fired.append(True)
                # Lands during the ~0.7 s move to the start of line 1, before any point of it.
                threading.Timer(0.1, self.service.pause_scan).start()
                threading.Timer(0.8, self.service.resume_scan).start()
            return motion_id

        self.adapter.move_to = move_to
        port = _PreviewPort([], self.service)
        self.service.set_output_port(port)

        scan = self._run(make_dto(), timeout=90.0)

        self.assertEqual(self.abandoned, [])  # no point acquired yet: nothing to abandon
        self.assertEqual(port.abandoned_seen, [])
        self.assertEqual(len(self.stops), 1)  # the motor is stopped all the same
        self._assert_whole_grid_once(scan)

    def test_pause_then_cancel_mid_line_commits_nothing_of_that_line(self):
        self._pause_in_line_1(lambda: threading.Timer(0.3, self.service.cancel_scan).start())

        scan = self._run(make_dto(), until="scancancelled", timeout=90.0)
        time.sleep(0.5)  # the loop leaves its wait and releases the streams

        self.assertEqual(scan.status, ScanStatus.CANCELLED)
        self.assertEqual([l.line_index for l in self._lines(scan)], [0])
        self.assertEqual(sorted(self.point_indices), [0, 1, 2, 3])  # only line 0, published whole
        self.assertFalse(self.continuous_service.is_acquisition_running())
        self.assertIsNone(self.continuous_service.get_controller())


class TestFlyScanLineIsNeverCommittedOnAnEndedScan(_FaithfulFlyStack):
    """Cancelled or failed scan: the line in progress is neither committed nor exported."""

    def _published_points(self):
        points = []
        self.event_bus.subscribe("scanpointacquired", lambda e: points.append(e.point_index))
        return points

    def test_cancel_mid_line_commits_nothing_of_that_line(self):
        points = self._published_points()
        self._on_first_preview_of_line(1, self.service.cancel_scan)

        scan = self._run(make_dto(), until="scancancelled", timeout=90.0)
        time.sleep(0.5)

        self.assertEqual(scan.status, ScanStatus.CANCELLED)
        self.assertEqual(self._committed_lines(scan), [0])
        self.assertEqual(sorted(points), [0, 1, 2, 3])

    def test_cancel_mid_line_stops_the_motor_like_a_pause(self):
        self._on_first_preview_of_line(1, self.service.cancel_scan)

        self._run(make_dto(), until="scancancelled", timeout=90.0)
        time.sleep(0.5)

        self.assertEqual(len(self.stops), 1)  # stopped at once, not left to finish its sweep
        self.assertFalse(self.adapter.is_moving())

    def test_failure_mid_line_stops_the_motor(self):
        def fail_the_scan():
            self.service._current_scan.fail("boom")
            self.service._publish_events(self.service._current_scan.domain_events)

        self._on_first_preview_of_line(1, fail_the_scan)

        self._run(make_dto(), until="scanfailed", timeout=90.0)
        time.sleep(0.5)

        self.assertEqual(len(self.stops), 1)
        self.assertFalse(self.adapter.is_moving())

    def test_cancel_on_the_last_line_commits_nothing_of_that_line(self):
        points = self._published_points()
        self._on_first_preview_of_line(2, self.service.cancel_scan)

        scan = self._run(make_dto(), until="scancancelled", timeout=90.0)
        time.sleep(0.5)

        self.assertEqual(self._committed_lines(scan), [0, 1])
        self.assertEqual(sorted(points), list(range(8)))
        self.assertFalse(self.continuous_service.is_acquisition_running())

    def test_failure_mid_line_commits_nothing_of_that_line(self):
        points = self._published_points()

        def fail_the_scan():
            self.service._current_scan.fail("boom")
            self.service._publish_events(self.service._current_scan.domain_events)

        self._on_first_preview_of_line(1, fail_the_scan)

        scan = self._run(make_dto(), until="scanfailed", timeout=90.0)
        time.sleep(0.5)

        self.assertEqual(scan.status, ScanStatus.FAILED)
        self.assertEqual(self._committed_lines(scan), [0])
        self.assertEqual(sorted(points), [0, 1, 2, 3])

    def _assert_published_points_are_exactly_the_committed_lines(self, scan, points):
        # Never N published points without their line: 0 or all of a line, and then it is committed.
        committed = self._committed_lines(scan)
        self.assertEqual(sorted(points), [line * 4 + k for line in committed for k in range(4)])

    def _cancel_in_point_handler(self, point_index, before=None):
        def on_point(event):
            if event.point_index == point_index:
                if before is not None:
                    before()
                self.service.cancel_scan()

        self.event_bus.subscribe("scanpointacquired", on_point)

    def test_cancel_in_the_handler_of_the_last_point_of_a_line_takes_effect_after_its_commit(self):
        points = self._published_points()
        self._cancel_in_point_handler(7)  # last point of line 1

        scan = self._run(make_dto(), until="scancancelled", timeout=90.0)
        time.sleep(0.5)

        self.assertEqual(scan.status, ScanStatus.CANCELLED)
        self.assertEqual(self._committed_lines(scan), [0, 1])
        self._assert_published_points_are_exactly_the_committed_lines(scan, points)

    def test_cancel_in_the_handler_of_the_first_point_of_a_line_takes_effect_after_its_commit(self):
        points = self._published_points()
        self._cancel_in_point_handler(4)  # first point of line 1: the 3 others must still go out

        scan = self._run(make_dto(), until="scancancelled", timeout=90.0)
        time.sleep(0.5)

        self.assertEqual(scan.status, ScanStatus.CANCELLED)
        self.assertEqual(self._committed_lines(scan), [0, 1])
        self._assert_published_points_are_exactly_the_committed_lines(scan, points)

    def test_pause_then_cancel_during_the_publication_take_effect_after_the_commit_in_order(self):
        points = self._published_points()
        paused = []
        self.event_bus.subscribe("scanpaused", paused.append)
        self._cancel_in_point_handler(5, before=self.service.pause_scan)

        scan = self._run(make_dto(), until="scancancelled", timeout=90.0)
        time.sleep(0.5)

        self.assertEqual(scan.status, ScanStatus.CANCELLED)
        self.assertEqual(self._committed_lines(scan), [0, 1])
        self._assert_published_points_are_exactly_the_committed_lines(scan, points)
        self.assertEqual(len(paused), 1)  # the pause was applied after the commit, then the cancel
        self.assertEqual(self.abandoned, [])  # the line was complete: nothing to abandon
        self.assertFalse(self.continuous_service.is_acquisition_running())

    def test_cancel_during_the_publication_of_the_last_line_is_ignored_and_the_scan_completes(self):
        completed, cancelled = [], []
        self.event_bus.subscribe("scancompleted", completed.append)
        self.event_bus.subscribe("scancancelled", cancelled.append)
        points = self._published_points()
        self._cancel_in_point_handler(8)  # first point of the last line

        scan = self._run(make_dto(), timeout=90.0)

        self.assertEqual(scan.status, ScanStatus.COMPLETED)
        self.assertEqual((len(completed), len(cancelled)), (1, 0))
        self.assertEqual(self._committed_lines(scan), [0, 1, 2])
        self._assert_published_points_are_exactly_the_committed_lines(scan, points)

    def test_cancel_after_the_last_point_is_ignored_and_the_scan_completes_once(self):
        completed, cancelled = [], []
        self.event_bus.subscribe("scancompleted", completed.append)
        self.event_bus.subscribe("scancancelled", cancelled.append)
        self.event_bus.subscribe("scanpointacquired", lambda e: self.service.cancel_scan() if e.point_index == 11 else None)

        scan = self._run(make_dto(), timeout=90.0)

        self.assertEqual(scan.status, ScanStatus.COMPLETED)
        self.assertEqual((len(completed), len(cancelled)), (1, 0))
        self.assertEqual(self._committed_lines(scan), [0, 1, 2])


class TestFlyScanExportHoldsOnlyCommittedLines(_FaithfulFlyStack):
    """The real ScanExportService over recording ports: no measurement row of an uncommitted line."""

    def setUp(self):
        super().setUp()
        excitation_service = ExcitationConfigurationService(MockExcitationPort(), self.event_bus)
        self.csv_port = _RecordingExportPort("csv", [])
        self.hdf5_port = _RecordingExportPort("hdf5", [])
        export = ScanExportService(
            self.event_bus,
            csv_export_port=self.csv_port,
            hdf5_export_port=self.hdf5_port,
            excitation_service=excitation_service,
            conditions_port=FakeAcquisitionConditionsPort(),
            software_provenance_port=FakeSoftwareProvenancePort(),
            usb_latency_timer_port=FakeUsbLatencyTimerPort(latency_ms=1.0),
        )
        export.configure_export(ExportConfigDTO(enabled=True, output_directory="", filename_base="fly"))

    def _rows(self, port):
        return sorted((round(r["x"], 6), round(r["y"], 6)) for r in port.points)

    def _committed_positions(self, scan):
        return sorted((round(p.position.x, 6), round(p.position.y, 6)) for line in self._lines(scan) for p in line.points)

    def test_cancel_during_the_publication_of_a_line_exports_no_orphan_point(self):
        self.event_bus.subscribe("scanpointacquired", lambda e: self.service.cancel_scan() if e.point_index == 5 else None)

        scan = self._run(make_dto(), until="scancancelled", timeout=90.0)
        time.sleep(0.5)

        for port in (self.csv_port, self.hdf5_port):
            self.assertEqual(len(port.points), 8)
            self.assertEqual(self._rows(port), self._committed_positions(scan))
            self.assertTrue(port.stopped)

    def test_preview_reaches_the_event_store_but_never_the_measurement_files(self):
        previews = []
        self.event_bus.subscribe("aefilinepreviewpointacquired", previews.append)
        # A pause abandons line 1: its previews never get a definitive point.
        self._on_first_preview_of_line(1, lambda: (
            self.service.pause_scan(), threading.Timer(0.5, self.service.resume_scan).start()))

        scan = self._run(make_dto(), timeout=90.0)

        self.assertGreater(len(previews), 12)  # the abandoned attempt of line 1 previewed too
        for port in (self.csv_port, self.hdf5_port):
            # Measurement rows: exactly the 12 committed grid points, none from a preview.
            self.assertEqual(len(port.points), 12)
            self.assertEqual(self._rows(port), self._committed_positions(scan))
            self.assertEqual(sorted(r["point_index"] for r in port.points), list(range(12)))
        # The event store (CSV port's _events.jsonl) keeps every preview and the abandon (safety net).
        recorded = [type(e).__name__ for e in self.csv_port.events]
        self.assertEqual(recorded.count("AefiLinePreviewPointAcquired"), len(previews))
        self.assertEqual(recorded.count("AefiLineAbandoned"), 1)

    def test_cancel_mid_sweep_exports_no_point_of_the_swept_line(self):
        self._on_first_preview_of_line(1, self.service.cancel_scan)

        scan = self._run(make_dto(), until="scancancelled", timeout=90.0)
        time.sleep(0.5)

        for port in (self.csv_port, self.hdf5_port):
            self.assertEqual(len(port.points), 4)
            self.assertEqual(self._rows(port), self._committed_positions(scan))


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
