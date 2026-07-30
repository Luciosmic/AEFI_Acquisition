import json
import shutil
import tempfile
import unittest
from pathlib import Path

import h5py

from infrastructure.persistence.hdf5_scan_export_port import Hdf5ScanExportPort


class TestHdf5ScanExportPortWritePoint(unittest.TestCase):
    """Points must land in resizable `/scan_data` datasets, readable back via h5py."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.port = Hdf5ScanExportPort()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_write_point_appends_to_scan_data_datasets(self):
        self.port.configure(str(self.tmp_dir), "scan", metadata={"scan_id": "abc"})
        self.port.start()

        self.port.write_point({
            "x": 1.0, "y": 2.0,
            "voltage_x_in_phase": 0.1, "voltage_x_quadrature": 0.2,
            "voltage_y_in_phase": 0.3, "voltage_y_quadrature": 0.4,
            "voltage_z_in_phase": 0.5, "voltage_z_quadrature": 0.6,
        })
        self.port.write_point({
            "x": 3.0, "y": 4.0,
            "voltage_x_in_phase": 1.1, "voltage_x_quadrature": 1.2,
            "voltage_y_in_phase": 1.3, "voltage_y_quadrature": 1.4,
            "voltage_z_in_phase": 1.5, "voltage_z_quadrature": 1.6,
        })
        self.port.stop()

        h5_files = list(self.tmp_dir.glob("*_stepScan_*/*_stepScan_scan.h5"))
        self.assertEqual(len(h5_files), 1)

        with h5py.File(h5_files[0], "r") as f:
            self.assertEqual(f.attrs["scan_id"], "abc")
            positions = f["scan_data/positions"][:]
            measurements = f["scan_data/measurements"][:]
            self.assertEqual(positions.shape, (2, 2))
            self.assertEqual(list(positions[0]), [1.0, 2.0])
            self.assertEqual(list(positions[1]), [3.0, 4.0])
            self.assertEqual(measurements.shape, (2, 6))
            self.assertEqual(list(measurements[0]), [0.1, 0.2, 0.3, 0.4, 0.5, 0.6])

    def test_get_output_path_is_none_before_configure_and_after_stop(self):
        self.assertIsNone(self.port.get_output_path())

        self.port.configure(str(self.tmp_dir), "scan", metadata={})
        self.port.start()
        path = self.port.get_output_path()
        self.assertIsNotNone(path)
        self.assertTrue(path.name.endswith("_stepScan_scan.h5"))

        self.port.stop()
        self.assertIsNone(self.port.get_output_path())


class TestHdf5ScanExportPortSharedTimestamp(unittest.TestCase):
    """A caller-supplied timestamp must be reused as-is, not regenerated."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_configure_with_explicit_timestamp_reuses_it(self):
        port = Hdf5ScanExportPort()
        port.configure(str(self.tmp_dir), "scan", metadata={}, timestamp="2024-01-01_000000")
        port.start()
        port.stop()

        h5_files = list(self.tmp_dir.glob("2024-01-01_000000_stepScan_scan/*.h5"))
        self.assertEqual(len(h5_files), 1)


class TestHdf5ScanExportPortMetadata(unittest.TestCase):
    """Acquisition metadata must land as a readable JSON sidecar, like the CSV port."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.port = Hdf5ScanExportPort()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_write_metadata_creates_json_sidecar(self):
        self.port.configure(str(self.tmp_dir), "scan", metadata={})
        self.port.start()
        self.port.write_metadata({"scan_id": "abc", "scan": {"pattern": "SERPENTINE"}})
        self.port.stop()

        json_files = list(self.tmp_dir.glob("*_stepScan_*/*_stepScan_scan_acquisition-parameters.json"))
        self.assertEqual(len(json_files), 1)

        with json_files[0].open(encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data, {"scan_id": "abc", "scan": {"pattern": "SERPENTINE"}})


if __name__ == "__main__":
    unittest.main()
