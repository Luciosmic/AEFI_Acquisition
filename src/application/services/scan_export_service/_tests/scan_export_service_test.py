import unittest
from typing import Any, Dict, List
from uuid import uuid4

from application.services.scan_export_service.scan_export_service import ScanExportService
from application.services.scan_export_service.dtos.scan_export_dtos import ExportConfigDTO
from application.services.scan_export_service.ports.i_scan_export_port import IScanExportPort
from application.services.scan_export_service.ports.i_acquisition_snapshot_port import IAcquisitionSnapshotPort
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
)

from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort

from domain.step_scan.events.scan_started.scan_started import ScanStarted
from domain.step_scan.value_objects.step_scan_config.step_scan_config import StepScanConfig
from domain.step_scan.value_objects.scan_zone.scan_zone import ScanZone
from domain.step_scan.value_objects.scan_pattern.scan_pattern import ScanPattern
from domain.step_scan.value_objects.scan_axis.scan_axis import ScanAxis
from domain.shared_kernel.value_objects.measurement_uncertainty.measurement_uncertainty import (
    MeasurementUncertainty,
)
from domain.shared_kernel.value_objects.excitation.excitation_mode import ExcitationMode
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

    def __init__(self) -> None:
        self.configured: Dict[str, Any] = {}
        self.points: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = None
        self.field_data_config: Dict[str, Any] = None
        self.field_points: List[Dict[str, Any]] = []
        self.started = False
        self.stopped = False

    def configure(self, directory, filename, metadata):
        self.configured = {"directory": directory, "filename": filename, "metadata": metadata}

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

    def stop(self):
        self.stopped = True


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


class TestScanExportServiceMetadata(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.export_port = FakeExportPort()
        excitation_service = ExcitationConfigurationService(MockExcitationPort(), self.event_bus)
        excitation_service.set_excitation(mode=ExcitationMode.X_DIR, level_percent=80.0, frequency=1000.0)

        class FakeSnapshotPort(IAcquisitionSnapshotPort):
            def read(self) -> Dict[str, Any]:
                return {"motion_last_config": {"speed_mode": "fast"}}

        self.service = ScanExportService(
            self.event_bus,
            csv_export_port=self.export_port,
            hdf5_export_port=self.export_port,
            excitation_service=excitation_service,
            acquisition_snapshot_port=FakeSnapshotPort(),
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
        self.assertEqual(metadata["excitation"]["level_percent"], 80.0)
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


if __name__ == "__main__":
    unittest.main()
