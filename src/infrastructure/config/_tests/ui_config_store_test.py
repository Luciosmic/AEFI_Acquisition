import json
import shutil
import tempfile
import unittest
from pathlib import Path

from infrastructure.config.ui_config_store import UIConfigStore


class TestUIConfigStore(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.store = UIConfigStore()
        self.store.SCAN_CONFIG_PATH = str(self.tmp_dir / "configs" / "scan_default_config.json")
        self.store.EXPORT_CONFIG_PATH = str(self.tmp_dir / "configs" / "export_default_config.json")
        self.store.EXPORT_CONFIG_TEMPLATE_PATH = str(self.tmp_dir / "templates" / "export_default_config.json")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_load_scan_config_returns_empty_dict_when_file_missing(self):
        self.assertEqual(self.store.load_scan_config(), {})

    def test_load_export_config_bootstraps_from_template_on_first_run(self):
        template_path = Path(self.store.EXPORT_CONFIG_TEMPLATE_PATH)
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(
            json.dumps({"enabled": True, "output_directory": "", "filename_base": "scan", "format": "CSV"}),
            encoding="utf-8",
        )

        export_config = self.store.load_export_config()

        self.assertTrue(Path(self.store.EXPORT_CONFIG_PATH).exists())
        self.assertEqual(export_config["format"], "CSV")

    def test_save_then_load_export_config_round_trips(self):
        self.store.save_export_config({"enabled": False, "filename_base": "custom", "output_directory": "d/", "format": "HDF5"})

        loaded = self.store.load_export_config()

        self.assertEqual(loaded["filename_base"], "custom")
        self.assertEqual(loaded["format"], "HDF5")


if __name__ == "__main__":
    unittest.main()
