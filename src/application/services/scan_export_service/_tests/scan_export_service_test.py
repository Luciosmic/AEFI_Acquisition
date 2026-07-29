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


class FakeExportPort(IScanExportPort):
    """Minimal in-memory double — records calls instead of touching disk."""

    def __init__(self) -> None:
        self.configured: Dict[str, Any] = {}
        self.points: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = None
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
        excitation_service = ExcitationConfigurationService(MockExcitationPort())
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


if __name__ == "__main__":
    unittest.main()
