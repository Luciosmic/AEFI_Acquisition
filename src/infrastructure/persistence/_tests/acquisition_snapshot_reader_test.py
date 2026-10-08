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

        self.assertEqual(set(snapshot), {"hardware_configuration", "hardware_settings"})
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
        (configs_dir / "motion_last_config.json").write_text(json.dumps({"speed_mode": "fast"}), encoding="utf-8")

        snapshot = self.reader.read()

        self.assertEqual(snapshot["motion_last_config"], {"speed_mode": "fast"})
        self.assertNotIn("aefi_device_hardware_identity", snapshot)  # template is no longer copied

    def _write_config(self, name: str, content: dict) -> None:
        configs_dir = Path(".aefi_acquisition/configs")
        configs_dir.mkdir(parents=True, exist_ok=True)
        (configs_dir / name).write_text(json.dumps(content), encoding="utf-8")

    def test_applied_adc_and_mcu_settings_are_exported_for_reproducibility(self):
        """n_avg and the ADC oversampling set the noise and the sample rate:
        an export without them cannot be reproduced."""
        self._write_config("ads131a04_default_config.json", {"oversampling_ratio": 4096, "clkin_divider": 2, "iclk_divider": 2})
        self._write_config("ads131a04_last_config.json", {"oversampling_ratio": 1024})
        self._write_config("mcu_default_config.json", {"n_avg": 127})
        self._write_config("mcu_last_config.json", {"n_avg": 16})

        settings = self.reader.read()["hardware_settings"]

        # What is applied = default + last resolved (last wins), not the last file alone.
        self.assertEqual(settings["ads131a04"], {"oversampling_ratio": 1024, "clkin_divider": 2, "iclk_divider": 2})
        self.assertEqual(settings["mcu"], {"n_avg": 16})

    def test_applied_dds_settings_merge_default_and_last_per_channel(self):
        self._write_config("ad9106_default_config.json", {"frequency_hz": 1000.0, "channels": {"1": {"gain": 0, "phase": 0}}})
        self._write_config("ad9106_last_config.json", {"channels": {"1": {"gain": 1100}}})

        ad9106 = self.reader.read()["hardware_settings"]["ad9106"]

        self.assertEqual(ad9106, {"frequency_hz": 1000.0, "channels": {"1": {"gain": 1100, "phase": 0}}})

    def test_unknown_settings_are_flagged_not_silently_dropped(self):
        settings = self.reader.read()["hardware_settings"]

        for name in ("ad9106", "ads131a04", "mcu"):
            self.assertIsNone(settings[name])
        self.assertEqual(len(settings["warnings"]), 3)

    def test_unreadable_settings_file_does_not_break_the_export(self):
        self._write_config("mcu_default_config.json", {"n_avg": 127})
        Path(".aefi_acquisition/configs/mcu_last_config.json").write_text("{not json", encoding="utf-8")

        settings = self.reader.read()["hardware_settings"]

        self.assertEqual(settings["mcu"], {"n_avg": 127})
        self.assertTrue(any("mcu_last_config.json" in w for w in settings["warnings"]))


if __name__ == "__main__":
    unittest.main()
