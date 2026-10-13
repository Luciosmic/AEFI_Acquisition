"""A bench without mm/pulse conversion refuses to start a scan, with a typed reason, before taking any control."""
import unittest

from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.motion_control_service.dtos.motion_conversion_status_dto import MotionConversionStatusDTO
from application.services.motion_control_service.ports.i_motion_conversion_status_port import (
    IMotionConversionStatusPort,
)
from application.services.scan_application_service.dtos.scan_dtos import LineScanConfigDTO, Scan2DConfigDTO
from application.services.scan_application_service.errors.scan_start_error import ScanRefusedBenchNotCalibrated
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.unit_of_work.in_memory_unit_of_work import InMemoryUnitOfWork


class UncalibratedMotionPort(MockMotionPort):
    def is_conversion_available(self) -> bool:
        return False


class FixedStatus(IMotionConversionStatusPort):
    def get_status(self) -> MotionConversionStatusDTO:
        return MotionConversionStatusDTO(
            is_available=False, motor_name="IGUS", missing_quantity="Pas par tour", where_to_enter="onglet Moteurs"
        )


class TestScanRefusedWhenBenchNotCalibrated(unittest.TestCase):
    def setUp(self):
        self.bus = InMemoryEventBus()
        self.service = ScanApplicationService(
            UncalibratedMotionPort(event_bus=self.bus, motion_delay_ms=1),
            AefiAcquisitionService(MockAefiAcquisitionExecutor(self.bus), MockAcquisitionPort()),
            self.bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=EventBusMotionSynchronizer(self.bus),
            unit_of_work=InMemoryUnitOfWork(self.bus),
            conversion_status=FixedStatus(),
        )
        self.started = []
        self.bus.subscribe("scanstarted", self.started.append)

    def test_refusal_is_typed_and_names_what_is_missing(self):
        refusal = self.service.get_start_refusal()

        self.assertIsInstance(refusal, ScanRefusedBenchNotCalibrated)
        self.assertEqual(refusal.missing_quantity, "Pas par tour")
        self.assertIn("Pas par tour", refusal.message)

    def test_grid_scan_is_refused_and_nothing_starts(self):
        dto = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=2, y_min=0, y_max=1, y_nb_points=2,
            scan_pattern="RASTER", stabilization_delay_ms=0, averaging_per_position=1, uncertainty_volts=1e-6,
        )

        self.assertFalse(self.service.execute_scan(dto))
        self.assertEqual(self.started, [])

    def test_line_scan_is_refused_and_nothing_starts(self):
        dto = LineScanConfigDTO(
            center_x=10.0, center_y=10.0, length_mm=5.0, n_points=3, theta_deg=0.0,
            stabilization_delay_ms=0, averaging_per_position=1,
        )

        self.assertFalse(self.service.execute_line_scan(dto))
        self.assertEqual(self.started, [])


if __name__ == "__main__":
    unittest.main()
