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
from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from domain.step_scan.value_objects.scan_status.scan_status import ScanStatus
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter
from infrastructure.hardware.arcus_performax_4EX.fake.fake_arcus_performax4ex_controller import (
    FakeArcusPerformax4EXController,
)
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


class _Stack(unittest.TestCase):
    def _service(self, motion_port):
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
        )

    def _run(self, dto, until="scancompleted", timeout=30.0):
        # Subscribe before execute: the scan runs on a background thread.
        done = threading.Event()
        self.event_bus.subscribe(until, lambda e: done.set())
        self.assertTrue(self.service.execute_scan(dto))
        self.assertTrue(done.wait(timeout=timeout), f"No {until} within timeout")
        return self.service._current_scan


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
        positions = [(p.position.x, p.position.y) for p in scan.points]
        self.assertEqual(positions, pytest.approx([
            (600.0, 600.0), (600.0, 610.0), (600.0, 620.0), (600.0, 630.0),
            (610.0, 630.0), (610.0, 620.0), (610.0, 610.0), (610.0, 600.0),
            (620.0, 600.0), (620.0, 610.0), (620.0, 620.0), (620.0, 630.0),
        ]))
        self.assertEqual([p.point_index for p in scan.points], list(range(12)))

    def test_points_are_emitted_while_the_line_is_swept(self):
        self._run(make_dto())

        # Each line: a move to its start, then the sweep. Points 0..3 belong
        # to the first sweep; at least one must be out before that sweep ends
        # (the first version emitted the whole line after the motion).
        first_sweep_done = [i for i, (kind, _) in enumerate(self.timeline) if kind == "motion_done"][1]
        live = [index for kind, index in self.timeline[:first_sweep_done] if kind == "point"]
        self.assertTrue(live, f"no point emitted during the first sweep: {self.timeline}")

    def test_fly_scan_releases_the_adc_stream_it_started(self):
        self._run(make_dto())

        self.assertFalse(self.continuous_service.is_acquisition_running())


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
        self.assertEqual(len(scan.points), 0)

    def test_fly_scan_rejects_differential_mode(self):
        self.assertFalse(self.service.execute_scan(make_dto(differential_mode=True)))
        self.assertIsNone(self.service._current_scan)


if __name__ == "__main__":
    unittest.main()
