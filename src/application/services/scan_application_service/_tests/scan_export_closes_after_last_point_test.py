"""
Integration: step-scan -> real ScanExportService -> two fake export ports.

Locks the ordering the export depends on: every point row is written BEFORE
ScanCompleted reaches the export (it closes the files on that event), whatever
component emits ScanCompleted.
"""
import threading
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
)
from application.services.scan_application_service.dtos.scan_dtos import Scan2DConfigDTO
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.scan_closure_handler.scan_closure_handler import ScanClosureHandler
from application.services.scan_export_service.dtos.scan_export_dtos import ExportConfigDTO
from application.services.scan_export_service.ports.i_scan_export_port import IScanExportPort
from application.services.scan_export_service.scan_export_service import ScanExportService
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from infrastructure.acquisition_conditions.fake.fake_acquisition_conditions_port import FakeAcquisitionConditionsPort
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.hardware.serial_link.fake.fake_usb_latency_timer_port import FakeUsbLatencyTimerPort
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.provenance.fake.fake_software_provenance_port import FakeSoftwareProvenancePort
from infrastructure.unit_of_work.in_memory_unit_of_work import InMemoryUnitOfWork


class _RecordingExportPort(IScanExportPort):
    """In-memory port noting, in a shared journal, when a point is written."""

    def __init__(self, name: str, journal: List[str]) -> None:
        self.name = name
        self.journal = journal
        self.points: List[Dict[str, Any]] = []
        self.events: List[Any] = []
        self.started = False
        self.stopped = False

    def configure(self, directory, filename, metadata, timestamp=None, acquisition_kind="stepScan"):
        pass

    def start(self):
        self.started = True

    def write_point(self, data):
        self.points.append(data)
        self.journal.append(f"write_point:{self.name}")

    def write_acquisition_parameters(self, parameters):
        pass

    def configure_field_data(self, n_components, probe_info):
        pass

    def write_field_point(self, data):
        pass

    def write_event(self, event):
        self.events.append(event)

    def get_output_path(self) -> Optional[Path]:
        return Path(f"/fake/{self.name}")

    def stop(self):
        self.stopped = True


class TestScanExportClosesAfterLastPoint(unittest.TestCase):
    def setUp(self):
        self.journal: List[str] = []
        self.event_bus = InMemoryEventBus()
        uow = InMemoryUnitOfWork(self.event_bus)
        ScanClosureHandler(self.event_bus, uow)

        excitation_service = ExcitationConfigurationService(MockExcitationPort(), self.event_bus)
        excitation_service.set_excitation(
            mode=ExcitationMode.X_DIR, level_s1_s2_percent=80.0, level_s3_s4_percent=60.0, frequency=1000.0
        )
        self.csv_port = _RecordingExportPort("csv", self.journal)
        self.hdf5_port = _RecordingExportPort("hdf5", self.journal)
        self.export_service = ScanExportService(
            self.event_bus,
            csv_export_port=self.csv_port,
            hdf5_export_port=self.hdf5_port,
            excitation_service=excitation_service,
            conditions_port=FakeAcquisitionConditionsPort(),
            software_provenance_port=FakeSoftwareProvenancePort(),
            usb_latency_timer_port=FakeUsbLatencyTimerPort(latency_ms=1.0),
        )
        self.export_service.configure_export(ExportConfigDTO(enabled=True, output_directory="", filename_base="scan"))

        self.done = threading.Event()

        def _on_completed(event):
            self.journal.append("ScanCompleted")
            self.done.set()

        self.event_bus.subscribe("scancompleted", _on_completed)
        self.service = ScanApplicationService(
            MockMotionPort(event_bus=self.event_bus, motion_delay_ms=1),
            AefiAcquisitionService(MockAefiAcquisitionExecutor(self.event_bus), MockAcquisitionPort()),
            self.event_bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=EventBusMotionSynchronizer(self.event_bus),
            excitation_service=excitation_service,
            unit_of_work=uow,
        )

    def _run(self, differential_mode: bool) -> None:
        dto = Scan2DConfigDTO(
            x_min=0, x_max=2, x_nb_points=3,
            y_min=0, y_max=1, y_nb_points=1,
            scan_pattern="RASTER", stabilization_delay_ms=0, averaging_per_position=1,
            uncertainty_volts=1e-6, differential_mode=differential_mode, differential_settle_delay_ms=0,
        )
        self.assertTrue(self.service.execute_scan(dto))
        self.assertTrue(self.done.wait(timeout=10.0), "scan did not complete")

    def test_every_point_is_written_to_both_ports_before_scan_completed_closes_the_export(self):
        self._run(differential_mode=False)

        self.assertEqual(len(self.csv_port.points), 3)
        self.assertEqual(len(self.hdf5_port.points), 3)
        last_write = max(i for i, entry in enumerate(self.journal) if entry.startswith("write_point"))
        self.assertLess(last_write, self.journal.index("ScanCompleted"))
        self.assertEqual(self.journal.count("ScanCompleted"), 1)
        for port in (self.csv_port, self.hdf5_port):
            self.assertTrue(port.stopped)
            self.assertEqual(type(port.events[-1]).__name__, "ScanCompleted")
        self.assertFalse(self.export_service._export_active)

    def test_differential_points_reach_the_export_with_their_baseline(self):
        self._run(differential_mode=True)

        for port in (self.csv_port, self.hdf5_port):
            self.assertEqual(len(port.points), 3)
            for row in port.points:
                self.assertIsNotNone(row["baseline_voltage_x_in_phase"])
                self.assertIsNotNone(row["baseline_voltage_z_quadrature"])


if __name__ == "__main__":
    unittest.main()
