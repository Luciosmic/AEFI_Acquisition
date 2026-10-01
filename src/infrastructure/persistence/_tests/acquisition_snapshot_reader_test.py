import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from domain.calibration.calibration import Calibration
from domain.calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement
from domain.calibration.entities.hardware_component_selection.hardware_component_selection import (
    HardwareComponentSelection,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)
from infrastructure.persistence.acquisition_snapshot_reader import AcquisitionSnapshotReader
from infrastructure.persistence.calibration.fake.fake_hardware_component_repository import (
    FakeHardwareComponentRepository,
)
from infrastructure.persistence.calibration.fake.fake_sensor_calibration_repository import (
    FakeSensorCalibrationRepository,
)
from infrastructure.persistence.calibration.fake.fake_source_geometry_calibration_repository import (
    FakeSourceGeometryCalibrationRepository,
)

CONDITIONING = HardwareComponentKind.CONDITIONING_ELECTRONICS_BOARD


class TestAcquisitionSnapshotReader(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.cwd = Path.cwd()
        self.addCleanup(lambda: os.chdir(self.cwd))
        os.chdir(self._tmp.name)
        self.components = FakeHardwareComponentRepository()
        self.geometries = FakeSourceGeometryCalibrationRepository()
        self.reader = AcquisitionSnapshotReader(
            hardware_component_repository=self.components,
            sensor_calibration_repository=FakeSensorCalibrationRepository(),
            source_geometry_calibration_repository=self.geometries,
        )

    def test_missing_config_files_are_omitted_and_empty_registries_are_flagged(self):
        snapshot = self.reader.read()

        self.assertEqual(set(snapshot), {"hardware_configuration"})
        hardware = snapshot["hardware_configuration"]
        for kind in HardwareComponentKind:
            self.assertIsNone(hardware[kind.value])
        self.assertEqual(len(hardware["warnings"]), len(HardwareComponentKind) + 2)
        self.assertIn("configuration incomplete", hardware["warnings"][0])

    def test_latest_source_geometry_is_exported_with_its_reconstructed_sphere_positions(self):
        measure = lambda values: tuple(CaliperMeasurement.from_resolution(v) for v in values)
        entry = Calibration().record_source_geometry_calibration_entry(
            measure((0.0196, 0.0196, 0.0195, 0.0195)),
            measure((0.11142, 0.10908, 0.08436, 0.08352, 0.08230, 0.08450)),
        )
        self.geometries.add(entry)

        reconstruction = self.reader.read()["hardware_configuration"]["source_frame_reconstruction"]

        self.assertEqual(reconstruction["source_geometry_entry_id"], str(entry.entry_id))
        x1, y1 = reconstruction["sphere_positions"]["S1"]  # x_neg_y_pos
        self.assertLess(x1, 0)
        self.assertGreater(y1, 0)
        self.assertEqual(list(reconstruction["distance_residuals"])[:2], ["D_S1_S2", "D_S3_S4"])
        json.dumps(reconstruction)  # plain JSON, no custom encoder needed

    def test_mounted_component_is_exported_from_domain_with_its_debt(self):
        self.components.add(
            Calibration().record_hardware_component_characterization(
                CONDITIONING, "Final_v4", {"gain": 9.8, "bandwidth_hz": 8e5}
            )
        )
        self.components.add_selection(HardwareComponentSelection.now(CONDITIONING, "Final_v4"))

        hardware = self.reader.read()["hardware_configuration"]

        board = hardware[CONDITIONING.value]
        self.assertEqual(board["component_name"], "Final_v4")
        self.assertEqual(
            board["characterization"], {"gain": 9.8, "bandwidth_hz": 8e5, "noise_density_v_per_sqrt_hz": None}
        )
        self.assertEqual(board["units"]["noise_density_v_per_sqrt_hz"], "V/√Hz")
        self.assertIn(
            "conditioning_electronics_board 'Final_v4': noise_density_v_per_sqrt_hz not characterized",
            hardware["warnings"],
        )
        json.dumps(hardware, default=str)  # what the export ports do

    def test_present_config_files_land_under_their_section_key(self):
        configs_dir = Path(".aefi_acquisition/configs")
        configs_dir.mkdir(parents=True)
        (configs_dir / "ad9106_last_config.json").write_text(json.dumps({"frequency_hz": 1000.0}), encoding="utf-8")

        snapshot = self.reader.read()

        self.assertEqual(snapshot["ad9106_last_config"], {"frequency_hz": 1000.0})
        self.assertNotIn("aefi_device_hardware_identity", snapshot)  # template is no longer copied


if __name__ == "__main__":
    unittest.main()
