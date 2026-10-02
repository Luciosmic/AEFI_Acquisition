"""
Integration test: a line scan (theta) runs through the same scan loop as the
grid scan, on the mock stack (no hardware).
"""
import threading
import unittest

import pytest

from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.dtos.scan_dtos import LineScanConfigDTO
from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from domain.step_scan.value_objects.scan_status.scan_status import ScanStatus
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort


def make_dto(**overrides):
    params = dict(
        center_x=600.0, center_y=600.0, length_mm=100.0, n_points=5, theta_deg=90.0,
        stabilization_delay_ms=0, averaging_per_position=2,
    )
    params.update(overrides)
    return LineScanConfigDTO(**params)


class TestScanLineExecution(unittest.TestCase):

    def setUp(self):
        self.event_bus = InMemoryEventBus()
        continuous_service = AefiAcquisitionService(
            MockAefiAcquisitionExecutor(self.event_bus),
            RandomNoiseAcquisitionPort(noise_std=0.0, seed=1),
        )
        self.started = []
        self.service = ScanApplicationService(
            MockMotionPort(event_bus=self.event_bus, motion_delay_ms=1),
            continuous_service,
            self.event_bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=EventBusMotionSynchronizer(self.event_bus),
            output_port=_StartRecordingOutputPort(self.started),
        )

    def _run(self, dto):
        # Subscribe before execute: the scan runs on a background thread.
        done = threading.Event()
        self.event_bus.subscribe("scancompleted", lambda e: done.set())
        self.assertTrue(self.service.execute_line_scan(dto))
        self.assertTrue(done.wait(timeout=10.0), "Line scan did not complete within timeout")
        return self.service._current_scan

    def test_line_scan_visits_the_line_points_in_order(self):
        scan = self._run(make_dto())

        self.assertEqual(scan.status, ScanStatus.COMPLETED)
        self.assertEqual(scan.expected_points, 5)
        positions = [(p.position.x, p.position.y) for p in scan.points]
        expected = [(600.0, 550.0), (600.0, 575.0), (600.0, 600.0), (600.0, 625.0), (600.0, 650.0)]
        self.assertEqual(positions, pytest.approx(expected))

    def test_scan_started_is_presented_as_a_line(self):
        self._run(make_dto(theta_deg=0.0))

        self.assertEqual(len(self.started), 1)
        config = self.started[0]
        self.assertEqual(config["scan_kind"], "line")
        self.assertEqual(config["points"], 5)
        self.assertEqual(config["n_points"], 5)
        self.assertEqual(config["theta_deg"], 0.0)
        self.assertAlmostEqual(config["start_x"], 550.0)
        self.assertAlmostEqual(config["end_x"], 650.0)

    def test_invalid_line_is_rejected_without_starting(self):
        # Line leaves the bench at x < 0.
        self.assertFalse(self.service.execute_line_scan(make_dto(center_x=10.0, theta_deg=0.0)))
        self.assertIsNone(self.service._current_scan)

    def test_differential_line_scan_requires_excitation_service(self):
        self.assertFalse(self.service.execute_line_scan(make_dto(differential_mode=True)))


class _StartRecordingOutputPort:
    """Minimal IScanOutputPort fake — records present_scan_started configs only."""

    def __init__(self, sink: list):
        self._sink = sink

    def present_scan_started(self, scan_id, config):
        self._sink.append(config)

    def __getattr__(self, name):
        return lambda *a, **k: None


if __name__ == "__main__":
    unittest.main()
