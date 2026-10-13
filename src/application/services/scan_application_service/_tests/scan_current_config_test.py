"""get_current_config: the config of the scan in progress, None before any scan (mock stack)."""
import threading
import unittest

from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.scan_application_service.dtos.scan_dtos import LineScanConfigDTO, Scan2DConfigDTO
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.scan_closure_handler.scan_closure_handler import ScanClosureHandler
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.unit_of_work.in_memory_unit_of_work import InMemoryUnitOfWork


class TestScanCurrentConfig(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        uow = InMemoryUnitOfWork(self.event_bus)
        ScanClosureHandler(self.event_bus, uow, ("aefipointacquired",))
        aefi = AefiAcquisitionService(MockAefiAcquisitionExecutor(self.event_bus), MockAcquisitionPort())
        self.service = ScanApplicationService(
            MockMotionPort(event_bus=self.event_bus, motion_delay_ms=5),
            aefi,
            self.event_bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=EventBusMotionSynchronizer(self.event_bus),
            unit_of_work=uow,
        )
        self.completed = threading.Event()
        self.event_bus.subscribe("scancompleted", lambda e: self.completed.set())

    def test_none_before_any_scan(self):
        self.assertIsNone(self.service.get_current_config())

    def test_step_scan_config_is_reported_with_grid_geometry(self):
        dto = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=2, y_min=0, y_max=2, y_nb_points=3,
            scan_pattern="RASTER", stabilization_delay_ms=7, averaging_per_position=2, uncertainty_volts=1e-6,
        )
        self.assertTrue(self.service.execute_scan(dto))
        self.assertTrue(self.completed.wait(10.0))

        snap = self.service.get_current_config()

        self.assertEqual(snap.scan_kind, "step")
        self.assertFalse(snap.fly_scan)
        self.assertEqual((snap.total_points, snap.stabilization_delay_ms, snap.averaging_per_position), (6, 7, 2))
        self.assertFalse(snap.differential_mode)
        self.assertEqual(snap.geometry["pattern"], "RASTER")
        self.assertEqual((snap.geometry["x_nb_points"], snap.geometry["y_nb_points"]), (2, 3))
        self.assertIsNotNone(snap.estimated_duration_s)
        self.assertIsNone(snap.excitation)  # no excitation service wired in this stack

    def test_line_scan_config_is_reported_with_line_geometry(self):
        dto = LineScanConfigDTO(
            center_x=10.0, center_y=20.0, length_mm=4.0, n_points=3, theta_deg=0.0,
            stabilization_delay_ms=0, averaging_per_position=1,
        )
        self.assertTrue(self.service.execute_line_scan(dto))
        self.assertTrue(self.completed.wait(10.0))

        snap = self.service.get_current_config()

        self.assertEqual(snap.scan_kind, "line")
        self.assertEqual(snap.total_points, 3)
        self.assertEqual((snap.geometry["center_x"], snap.geometry["length_mm"]), (10.0, 4.0))
        self.assertIsNone(snap.estimated_duration_s)


if __name__ == "__main__":
    unittest.main()
