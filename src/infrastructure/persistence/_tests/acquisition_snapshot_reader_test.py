import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from infrastructure.persistence.acquisition_snapshot_reader import AcquisitionSnapshotReader


class TestAcquisitionSnapshotReader(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.cwd = Path.cwd()
        self.addCleanup(lambda: os.chdir(self.cwd))
        os.chdir(self._tmp.name)
        self.reader = AcquisitionSnapshotReader()

    def test_missing_files_are_silently_omitted(self):
        self.assertEqual(self.reader.read(), {})

    def test_present_files_land_under_their_section_key(self):
        configs_dir = Path(".aefi_acquisition/configs")
        configs_dir.mkdir(parents=True)
        (configs_dir / "ad9106_last_config.json").write_text(
            json.dumps({"frequency_hz": 1000.0}), encoding="utf-8"
        )
        templates_dir = Path("config_templates")
        templates_dir.mkdir(parents=True)
        (templates_dir / "aefi_device_config.json").write_text(
            json.dumps({"schema_version": "2.0"}), encoding="utf-8"
        )

        snapshot = self.reader.read()

        self.assertEqual(snapshot["ad9106_last_config"], {"frequency_hz": 1000.0})
        self.assertEqual(snapshot["aefi_device_hardware_identity"], {"schema_version": "2.0"})
        self.assertNotIn("motion_last_config", snapshot)
        self.assertNotIn("electric_field_probe_connection_defaults", snapshot)


if __name__ == "__main__":
    unittest.main()
