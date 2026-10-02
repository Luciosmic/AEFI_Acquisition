import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from infrastructure.persistence.csv_scan_export_port import CsvScanExportPort
from infrastructure.persistence._tests import make_scan_acquisition_parameters


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
        # per acquisition), named timestamp_stepScan_<name>_<device>.
        main_files = list(self.tmp_dir.glob("*_stepScan_*/*_stepScan_scan_aefi.csv"))
        field_files = list(self.tmp_dir.glob("*_stepScan_*/*_stepScan_scan_narda_ep600.csv"))
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

    def test_write_field_point_expands_baseline_components(self):
        self.port.configure(str(self.tmp_dir), "scan", metadata={})
        self.port.start()
        self.port.configure_field_data(n_components=1, probe_info={"probe_label": "narda_ep600", "n_components": 1})

        self.port.write_field_point({
            "scan_id": "abc",
            "point_index": 0,
            "x": 1.0,
            "y": 2.0,
            "field_components": (0.9,),
            "field_std_dev_components": None,
            "baseline_field_components": (0.1,),
            "baseline_field_std_dev_components": None,
        })
        self.port.stop()

        field_files = list(self.tmp_dir.glob("*_stepScan_*/*_stepScan_scan_narda_ep600.csv"))
        with field_files[0].open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        row = rows[0]
        self.assertEqual(row["field_component_0"], "0.9")
        self.assertEqual(row["baseline_field_component_0"], "0.1")
        self.assertNotIn("baseline_field_components", row)

    def test_write_field_point_no_baseline_columns_when_not_differential(self):
        # ponytail: no baseline_field_component_N column when the scan never
        # provides baseline data — first-row-establishes-columns, same as
        # every other dynamic field on this port. Upgrade to always-present
        # empty columns if a downstream consumer needs a stable schema
        # across differential/non-differential exports.
        self.port.configure(str(self.tmp_dir), "scan", metadata={})
        self.port.start()
        self.port.configure_field_data(n_components=1, probe_info={"probe_label": "narda_ep600", "n_components": 1})

        self.port.write_field_point({
            "scan_id": "abc",
            "point_index": 0,
            "x": 1.0,
            "y": 2.0,
            "field_components": (0.9,),
            "field_std_dev_components": None,
            "baseline_field_components": None,
            "baseline_field_std_dev_components": None,
        })
        self.port.stop()

        field_files = list(self.tmp_dir.glob("*_stepScan_*/*_stepScan_scan_narda_ep600.csv"))
        with field_files[0].open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        self.assertNotIn("baseline_field_component_0", rows[0])


class TestCsvScanExportPortMetadata(unittest.TestCase):
    """Acquisition metadata must land as a readable JSON in the acquisition folder."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.port = CsvScanExportPort()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _document(self):
        json_files = list(self.tmp_dir.glob("*_stepScan_*/*_stepScan_scan_acquisition-parameters.json"))
        self.assertEqual(len(json_files), 1)
        with json_files[0].open(encoding="utf-8") as f:
            return json.load(f)

    def test_start_document_is_schema_1_0_and_still_running(self):
        self.port.configure(str(self.tmp_dir), "scan", metadata={})
        self.port.start()
        self.port.write_acquisition_parameters(make_scan_acquisition_parameters())

        data = self._document()
        self.port.stop()
        self.assertEqual(data["schema"]["version"], "1.0")
        self.assertEqual(data["provenance"]["activity"]["status"], "running")
        self.assertEqual(data["procedure"]["step_scan"]["pattern"], "SERPENTINE")
        self.assertEqual(
            [f["name"] for f in data["data"]["files"]], ["acquisition-parameters.json"]
        )  # files are listed only once the acquisition has ended

    def test_final_document_written_after_stop_lists_and_hashes_every_file(self):
        self.port.configure(str(self.tmp_dir), "scan", metadata={})
        self.port.start()
        self.port.write_point({"x": 1.0, "y": 2.0})
        self.port.stop()
        self.port.write_acquisition_parameters(make_scan_acquisition_parameters(ended=True))

        data = self._document()
        self.assertEqual(data["provenance"]["activity"]["status"], "completed")
        files = {f["name"].rsplit("_", 1)[-1]: f for f in data["data"]["files"]}
        self.assertIn("aefi.csv", files)
        self.assertIn("events.jsonl", files)
        self.assertEqual(len(files["aefi.csv"]["sha256"]), 64)
        self.assertEqual(files["aefi.csv"]["format"], "CSV")


class TestCsvScanExportPortLogs(unittest.TestCase):
    """App logs emitted during a scan must land next to its data."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.port = CsvScanExportPort()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_logs_between_start_and_stop_land_in_acquisition_folder(self):
        import logging
        logging.getLogger().setLevel(logging.INFO)
        self.port.configure(str(self.tmp_dir), "scan", metadata={})
        self.port.start()
        logging.getLogger("some.module").info("during scan")
        self.port.stop()
        logging.getLogger("some.module").info("after scan")

        log_files = list(self.tmp_dir.glob("*_stepScan_*/*_stepScan_scan_logs.log"))
        self.assertEqual(len(log_files), 1)
        content = log_files[0].read_text(encoding="utf-8")
        self.assertIn("during scan", content)
        self.assertNotIn("after scan", content)

    def test_write_event_appends_jsonl_line_in_acquisition_folder(self):
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class _SampleEvent:
            scan_id: str

        self.port.configure(str(self.tmp_dir), "scan", metadata={})
        self.port.start()
        self.port.write_event(_SampleEvent(scan_id="abc"))
        self.port.write_event(_SampleEvent(scan_id="abc"))
        self.port.stop()

        event_files = list(self.tmp_dir.glob("*_stepScan_*/*_stepScan_scan_events.jsonl"))
        self.assertEqual(len(event_files), 1)
        lines = event_files[0].read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0]), {"event_type": "_SampleEvent", "scan_id": "abc"})


if __name__ == "__main__":
    unittest.main()
