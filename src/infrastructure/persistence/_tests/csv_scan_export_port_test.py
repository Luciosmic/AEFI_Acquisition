import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from infrastructure.persistence.csv_scan_export_port import CsvScanExportPort


class TestCsvScanExportPortFieldData(unittest.TestCase):
    """Electric field data must land in a readable sidecar CSV, flattened per component."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.port = CsvScanExportPort()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_write_field_point_creates_separate_file_named_after_probe(self):
        self.port.configure(str(self.tmp_dir), "scan", metadata={})
        self.port.start()
        self.port.configure_field_data(n_components=2, probe_info={"probe_label": "narda_ep600", "n_components": 2})

        self.port.write_field_point({
            "scan_id": "abc",
            "point_index": 0,
            "x": 1.0,
            "y": 2.0,
            "field_components": (3.0, 4.0),
            "field_std_dev_components": (0.1, 0.2),
        })
        self.port.stop()

        # Both files land in the same acquisition folder (one bounded context
        # per acquisition), named timestamp_stepScan_<device>_<name>.
        main_files = list(self.tmp_dir.glob("*_stepScan_*/*_stepScan_aefi_scan.csv"))
        field_files = list(self.tmp_dir.glob("*_stepScan_*/*_stepScan_narda_ep600_scan.csv"))
        self.assertEqual(len(field_files), 1)
        # Field data must be a distinct file from the main aefi_device export.
        self.assertNotEqual(main_files, field_files)
        self.assertEqual(main_files[0].parent, field_files[0].parent)

        with field_files[0].open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["field_component_0"], "3.0")
        self.assertEqual(row["field_component_1"], "4.0")
        self.assertEqual(row["field_std_dev_component_0"], "0.1")
        self.assertEqual(row["field_std_dev_component_1"], "0.2")
        self.assertNotIn("field_components", row)


class TestCsvScanExportPortMetadata(unittest.TestCase):
    """Acquisition metadata must land as a readable JSON in the acquisition folder."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.port = CsvScanExportPort()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_write_metadata_creates_json_in_acquisition_folder(self):
        self.port.configure(str(self.tmp_dir), "scan", metadata={})
        self.port.start()
        self.port.write_metadata({"scan_id": "abc", "scan": {"pattern": "SERPENTINE"}})
        self.port.stop()

        json_files = list(self.tmp_dir.glob("*_stepScan_*/*_stepScan_scan.json"))
        self.assertEqual(len(json_files), 1)

        with json_files[0].open(encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data, {"scan_id": "abc", "scan": {"pattern": "SERPENTINE"}})


if __name__ == "__main__":
    unittest.main()
