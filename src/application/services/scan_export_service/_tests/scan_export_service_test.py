import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from application.services.scan_export_service.scan_export_service import ScanExportService
from application.services.scan_export_service.dtos.scan_export_dtos import ExportConfigDTO
from application.services.scan_export_service.ports.i_scan_export_port import IScanExportPort
from application.services.scan_export_service.ports.i_acquisition_snapshot_port import IAcquisitionSnapshotPort
from application.services.scan_export_service.ports.i_post_processing_port import IPostProcessingPort
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
)

from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.execution.fake.fake_thread_pool_task_runner import FakeThreadPoolTaskRunner

from domain.step_scan.events.scan_started.scan_started import ScanStarted
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from domain.step_scan.events.scan_failed.scan_failed import ScanFailed
from domain.step_scan.events.scan_cancelled.scan_cancelled import ScanCancelled
from domain.step_scan.events.scan_point_acquired.scan_point_acquired import ScanPointAcquired
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.step_scan.value_objects.step_scan_config.step_scan_config import StepScanConfig
from domain.step_scan.value_objects.scan_zone.scan_zone import ScanZone
from domain.step_scan.value_objects.scan_pattern.scan_pattern import ScanPattern
from domain.step_scan.value_objects.scan_axis.scan_axis import ScanAxis
from domain.shared_kernel.value_objects.measurement_uncertainty.measurement_uncertainty import (
    MeasurementUncertainty,
)
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from domain.electric_field_probe.electric_field_probe import ElectricFieldProbe
from domain.electric_field_probe.events.electric_field_probe_connection_changed.electric_field_probe_connection_changed import (
    ElectricFieldProbeConnectionChanged,
)
from domain.step_scan.events.electric_field_scan_point_acquired.electric_field_scan_point_acquired import (
    ElectricFieldScanPointAcquired,
)
from domain.electric_field_probe.value_objects.field_measurement.field_measurement import FieldMeasurement
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


class FakeExportPort(IScanExportPort):
    """Minimal in-memory double — records calls instead of touching disk."""

    def __init__(self, output_path: Path = Path("/fake/scan.out")) -> None:
        self.configured: Dict[str, Any] = {}
        self.points: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = None
        self.field_data_config: Dict[str, Any] = None
        self.field_points: List[Dict[str, Any]] = []
        self.started = False
        self.stopped = False
        self._output_path = output_path

    def configure(self, directory, filename, metadata, timestamp=None):
        self.configured = {
            "directory": directory, "filename": filename, "metadata": metadata, "timestamp": timestamp,
        }

    def start(self):
        self.started = True

    def write_point(self, data):
        self.points.append(data)

    def write_metadata(self, metadata):
        self.metadata = metadata

    def configure_field_data(self, n_components, probe_info):
        self.field_data_config = {"n_components": n_components, "probe_info": probe_info}

    def write_field_point(self, data):
        self.field_points.append(data)

    def get_output_path(self) -> Optional[Path]:
        return self._output_path

    def stop(self):
        self.stopped = True


class FakePostProcessingPort(IPostProcessingPort):
    """Records `run()` calls instead of driving the real post-processor."""

    def __init__(self) -> None:
        self.calls: List[Any] = []

    def run(self, csv_path: Path, hdf5_path: Path) -> None:
        self.calls.append((csv_path, hdf5_path))


def _make_scan_started_event():
    zone = ScanZone(x_min=435.0, x_max=835.0, y_min=435.0, y_max=835.0)
    config = StepScanConfig(
        scan_zone=zone,
        x_nb_points=21,
        y_nb_points=21,
        scan_pattern=ScanPattern.SERPENTINE,
        stabilization_delay_ms=300,
        averaging_per_position=10,
        measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=1e-6),
        scan_axis=ScanAxis.Y,
    )
    return ScanStarted(scan_id=uuid4(), config=config)


def _make_scan_point_acquired_event():
    return ScanPointAcquired(
        scan_id=uuid4(),
        point_index=0,
        position=Position2D(x=1.0, y=2.0),
        measurement=AefiVoltageMeasurement(
            voltage_x_in_phase=0.1, voltage_x_quadrature=0.2,
            voltage_y_in_phase=0.3, voltage_y_quadrature=0.4,
            voltage_z_in_phase=0.5, voltage_z_quadrature=0.6,
            timestamp=datetime.now(),
        ),
    )


class TestScanExportServiceMetadata(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.export_port = FakeExportPort(output_path=Path("/fake/scan.csv"))
        self.hdf5_export_port = FakeExportPort(output_path=Path("/fake/scan.h5"))
        self.post_processing_port = FakePostProcessingPort()
        excitation_service = ExcitationConfigurationService(MockExcitationPort(), self.event_bus)
        excitation_service.set_excitation(
            mode=ExcitationMode.X_DIR, level_s1_s2_percent=80.0, level_s3_s4_percent=60.0, frequency=1000.0
        )

        class FakeSnapshotPort(IAcquisitionSnapshotPort):
            def read(self) -> Dict[str, Any]:
                return {"motion_last_config": {"speed_mode": "fast"}}

        self.service = ScanExportService(
            self.event_bus,
            csv_export_port=self.export_port,
            hdf5_export_port=self.hdf5_export_port,
            excitation_service=excitation_service,
            acquisition_snapshot_port=FakeSnapshotPort(),
            post_processing_port=self.post_processing_port,
            task_runner=FakeThreadPoolTaskRunner(),
        )
        self.service.configure_export(
            ExportConfigDTO(enabled=True, output_directory="", filename_base="scan")
        )

    def test_write_metadata_receives_scan_excitation_snapshot(self):
        self.event_bus.publish("scanstarted", _make_scan_started_event())

        self.assertIsNotNone(self.export_port.metadata)
        metadata = self.export_port.metadata
        self.assertEqual(metadata["scan"]["pattern"], "SERPENTINE")
        self.assertEqual(metadata["scan"]["scan_axis"], "Y")
        self.assertEqual(metadata["excitation"]["level_s1_s2_percent"], 80.0)
        self.assertEqual(metadata["excitation"]["level_s3_s4_percent"], 60.0)
        self.assertEqual(metadata["motion_last_config"], {"speed_mode": "fast"})
        self.assertIsNone(metadata["electric_field_probe"])

    def test_probe_connection_event_is_cached_into_next_metadata(self):
        probe = ElectricFieldProbe(
            brand="Narda", model="EP-601", serial_number="SN123",
            axis_labels=("x", "y", "z"), battery_percentage=62.0,
        )
        self.event_bus.publish(
            "electricfieldprobeconnectionchanged",
            ElectricFieldProbeConnectionChanged(connected=True, probe=probe),
        )

        self.event_bus.publish("scanstarted", _make_scan_started_event())

        probe_metadata = self.export_port.metadata["electric_field_probe"]
        self.assertEqual(probe_metadata["serial_number"], "SN123")
        self.assertEqual(probe_metadata["axis_labels"], ["x", "y", "z"])

    def test_field_sidecar_label_is_derived_from_connected_probe(self):
        probe = ElectricFieldProbe(
            brand="Narda", model="EP-601", serial_number="SN123",
            axis_labels=("X", "Y", "Z"),
        )
        self.event_bus.publish(
            "electricfieldprobeconnectionchanged",
            ElectricFieldProbeConnectionChanged(connected=True, probe=probe),
        )
        self.event_bus.publish("scanstarted", _make_scan_started_event())

        self.event_bus.publish(
            "electricfieldscanpointacquired",
            ElectricFieldScanPointAcquired(
                scan_id=uuid4(), point_index=0, position=Position2D(x=1.0, y=2.0),
                field_measurement=FieldMeasurement(components=(1.0, 2.0, 3.0), timestamp=None),
            ),
        )

        self.assertEqual(self.export_port.field_data_config["probe_info"]["probe_label"], "narda-ep601")
        self.assertEqual(self.export_port.field_data_config["probe_info"]["axis_labels"], ("x", "y", "z"))

    def test_scan_exports_to_both_csv_and_hdf5_simultaneously(self):
        self.event_bus.publish("scanstarted", _make_scan_started_event())
        self.event_bus.publish(
            "scanpointacquired",
            _make_scan_point_acquired_event(),
        )

        self.assertTrue(self.export_port.started)
        self.assertTrue(self.hdf5_export_port.started)
        self.assertEqual(len(self.export_port.points), 1)
        self.assertEqual(len(self.hdf5_export_port.points), 1)
        # Both ports must share one acquisition folder — same timestamp.
        self.assertEqual(
            self.export_port.configured["timestamp"], self.hdf5_export_port.configured["timestamp"]
        )

    def test_post_processing_runs_on_scan_completed_with_both_output_paths(self):
        started = _make_scan_started_event()
        self.event_bus.publish("scanstarted", started)
        self.event_bus.publish("scancompleted", ScanCompleted(scan_id=started.scan_id, total_points=1))

        self.assertEqual(self.post_processing_port.calls, [(Path("/fake/scan.csv"), Path("/fake/scan.h5"))])
        self.assertTrue(self.export_port.stopped)
        self.assertTrue(self.hdf5_export_port.stopped)

    def test_post_processing_does_not_run_on_scan_cancelled(self):
        started = _make_scan_started_event()
        self.event_bus.publish("scanstarted", started)
        self.event_bus.publish("scancancelled", ScanCancelled(scan_id=started.scan_id))

        self.assertEqual(self.post_processing_port.calls, [])
        self.assertTrue(self.export_port.stopped)

    def test_non_differential_point_has_empty_baseline_columns(self):
        self.event_bus.publish("scanstarted", _make_scan_started_event())
        self.event_bus.publish("scanpointacquired", _make_scan_point_acquired_event())

        row = self.export_port.points[0]
        self.assertIsNone(row["baseline_voltage_x_in_phase"])

    def test_differential_point_carries_baseline_columns(self):
        self.event_bus.publish("scanstarted", _make_scan_started_event())
        event = ScanPointAcquired(
            scan_id=uuid4(),
            point_index=0,
            position=Position2D(x=1.0, y=2.0),
            measurement=AefiVoltageMeasurement(
                voltage_x_in_phase=0.9, voltage_x_quadrature=0.0,
                voltage_y_in_phase=0.0, voltage_y_quadrature=0.0,
                voltage_z_in_phase=0.0, voltage_z_quadrature=0.0,
                timestamp=datetime.now(),
            ),
            baseline_measurement=AefiVoltageMeasurement(
                voltage_x_in_phase=0.1, voltage_x_quadrature=0.0,
                voltage_y_in_phase=0.0, voltage_y_quadrature=0.0,
                voltage_z_in_phase=0.0, voltage_z_quadrature=0.0,
                timestamp=datetime.now(),
            ),
        )
        self.event_bus.publish("scanpointacquired", event)

        row = self.export_port.points[0]
        self.assertEqual(row["baseline_voltage_x_in_phase"], 0.1)
        self.assertEqual(row["voltage_x_in_phase"], 0.9)

    def test_differential_field_point_carries_baseline_columns(self):
        self.event_bus.publish("scanstarted", _make_scan_started_event())
        event = ElectricFieldScanPointAcquired(
            scan_id=uuid4(), point_index=0, position=Position2D(x=1.0, y=2.0),
            field_measurement=FieldMeasurement(components=(0.9,), timestamp=None),
            baseline_field_measurement=FieldMeasurement(components=(0.1,), timestamp=None),
        )
        self.event_bus.publish("electricfieldscanpointacquired", event)

        row = self.export_port.field_points[0]
        self.assertEqual(row["baseline_field_components"], (0.1,))


class TestScanExportServiceZeroPointCleanup(unittest.TestCase):
    """A scan that fails/is cancelled before any point is acquired must not
    leave an empty acquisition folder (0-row CSV, near-empty HDF5) behind —
    see _system/ops/tasks.md discussion on export-folder clutter."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.acquisition_dir = self.tmp_dir / "2024-01-01_000000_stepScan_scan"
        self.acquisition_dir.mkdir(parents=True)
        self.csv_path = self.acquisition_dir / "2024-01-01_000000_stepScan_scan_aefi.csv"
        self.hdf5_path = self.acquisition_dir / "2024-01-01_000000_stepScan_scan.h5"
        self.csv_path.write_text("")
        self.hdf5_path.write_bytes(b"")
        (self.acquisition_dir / "2024-01-01_000000_stepScan_scan_acquisition-parameters.json").write_text("{}")

        self.event_bus = InMemoryEventBus()
        self.csv_port = FakeExportPort(output_path=self.csv_path)
        self.hdf5_port = FakeExportPort(output_path=self.hdf5_path)
        excitation_service = ExcitationConfigurationService(MockExcitationPort(), self.event_bus)

        class FakeSnapshotPort(IAcquisitionSnapshotPort):
            def read(self) -> Dict[str, Any]:
                return {}

        self.service = ScanExportService(
            self.event_bus,
            csv_export_port=self.csv_port,
            hdf5_export_port=self.hdf5_port,
            excitation_service=excitation_service,
            acquisition_snapshot_port=FakeSnapshotPort(),
        )
        self.service.configure_export(
            ExportConfigDTO(enabled=True, output_directory="", filename_base="scan")
        )

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_zero_point_scan_removes_acquisition_folder_on_fail(self):
        started = _make_scan_started_event()
        self.event_bus.publish("scanstarted", started)
        # No ScanPointAcquired published — scan failed before any point.
        self.event_bus.publish(
            "scanfailed", ScanFailed(scan_id=started.scan_id, reason="motion error")
        )

        self.assertFalse(self.acquisition_dir.exists())

    def test_zero_point_scan_removes_acquisition_folder_on_cancel(self):
        started = _make_scan_started_event()
        self.event_bus.publish("scanstarted", started)
        self.event_bus.publish("scancancelled", ScanCancelled(scan_id=started.scan_id))

        self.assertFalse(self.acquisition_dir.exists())

    def test_scan_with_points_keeps_acquisition_folder_on_cancel(self):
        started = _make_scan_started_event()
        self.event_bus.publish("scanstarted", started)
        self.event_bus.publish("scanpointacquired", _make_scan_point_acquired_event())
        self.event_bus.publish("scancancelled", ScanCancelled(scan_id=started.scan_id))

        self.assertTrue(self.acquisition_dir.exists())


if __name__ == "__main__":
    unittest.main()
