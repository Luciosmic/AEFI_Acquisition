import csv
import hashlib
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputCharacterizationDTO,
    AcquisitionThroughputPointDTO,
    AcquisitionThroughputSampleDTO,
)
from infrastructure.persistence.acquisition_throughput._tests import make_acquisition_parameters_dto
from infrastructure.persistence.acquisition_throughput.acquisition_parameters_v1_serializer import COLUMNS
from infrastructure.persistence.acquisition_throughput.csv_acquisition_throughput_export_port import (
    CsvAcquisitionThroughputExportPort,
)


def point(n_avg):
    return AcquisitionThroughputPointDTO(
        n_avg=n_avg, sample_period_s=0.01 + n_avg / 1000, sample_rate_per_s=1 / (0.01 + n_avg / 1000),
        adc_conversions_per_s=n_avg / (0.01 + n_avg / 1000), noise_v_rms=(1e-6,) * 6, noise_rms_v=1e-6,
        noise_in_one_second_v=1e-7,
    )


RESULT = AcquisitionThroughputCharacterizationDTO(
    points=(point(1), point(8)), overhead_s=0.01, adc_output_rate_hz=1000.0, fit_max_relative_residual=0.0,
    recommended_n_avg=8, noise_relative_uncertainty=0.1, oversampling_ratio=4096, excitation="coupée", export_path=None,
)
SAMPLES = [
    AcquisitionThroughputSampleDTO(n_avg=n, sample_index=i, timestamp=datetime(2026, 10, 2, 12, 0, i), values_v=(0.0,) * 6)
    for n in (1, 8) for i in range(3)
]
CLOCK = datetime(2026, 10, 2, 14, 3, 11)
PARAMETERS = make_acquisition_parameters_dto()


class TestCsvAcquisitionThroughputExportPort(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.port = CsvAcquisitionThroughputExportPort(base_output_dir=Path(self._tmp.name), clock=lambda: CLOCK)

    def tearDown(self):
        self._tmp.cleanup()

    def _open(self):
        opened = self.port.open_export(4096, "coupée")
        self.assertTrue(opened.is_success)
        return Path(opened.value)

    def test_opens_a_dated_folder(self):
        self.assertEqual(self._open().name, "2026-10-02_140311_mcuThroughput_osr4096_excitation-coupée")

    def test_writes_summary_and_samples_and_describes_them(self):
        folder = self._open()
        result = self.port.export(str(folder), RESULT, SAMPLES)

        self.assertTrue(result.is_success)
        summary_lines = (folder / "summary.csv").read_text(encoding="utf-8").splitlines()
        self.assertTrue(any("recommended_n_avg,8" in line for line in summary_lines if line.startswith("#")))
        rows = list(csv.DictReader(line for line in summary_lines if not line.startswith("#")))
        self.assertEqual([r["n_avg"] for r in rows], ["1", "8"])
        with open(folder / "samples.csv", encoding="utf-8") as f:
            samples = list(csv.DictReader(f))
        self.assertEqual(len(samples), 6)
        self.assertRegex(samples[0]["timestamp"], r"[+-]\d\d:\d\d$")  # ISO 8601 with offset
        summary, samples_file = result.value
        self.assertEqual(summary.name, "summary.csv")
        self.assertEqual(samples_file.byte_size, (folder / "samples.csv").stat().st_size)
        self.assertEqual(samples_file.sha256, hashlib.sha256((folder / "samples.csv").read_bytes()).hexdigest())

    def test_every_written_column_is_described_in_the_parameters(self):
        folder = self._open()
        self.port.export(str(folder), RESULT, SAMPLES)
        for name in ("summary.csv", "samples.csv"):
            header = next(line for line in (folder / name).read_text(encoding="utf-8").splitlines() if not line.startswith("#"))
            for column in header.split(","):
                with self.subTest(file=name, column=column):
                    self.assertIn(column, COLUMNS)

    def test_writes_the_acquisition_parameters_json_and_rewrites_it(self):
        folder = self._open()
        running = make_acquisition_parameters_dto(files=())
        self.assertTrue(self.port.write_acquisition_parameters(str(folder), running).is_success)
        self.assertTrue(self.port.write_acquisition_parameters(str(folder), PARAMETERS).is_success)

        document = json.loads((folder / "acquisition-parameters.json").read_text(encoding="utf-8"))
        self.assertEqual(document["schema"]["version"], "1.0")
        self.assertEqual(document["provenance"]["activity"]["id"], "act-1")
        self.assertEqual(len(document["data"]["files"]), 3)
        self.assertEqual([p.name for p in folder.iterdir()], ["acquisition-parameters.json"])  # no temp file left

    def test_unwritable_location_is_a_failure(self):
        blocker = Path(self._tmp.name) / "not_a_dir"
        blocker.write_text("x")
        port = CsvAcquisitionThroughputExportPort(base_output_dir=blocker)
        self.assertTrue(port.open_export(4096, "coupée").is_failure)
        self.assertTrue(port.export(str(blocker / "missing"), RESULT, SAMPLES).is_failure)
        self.assertTrue(port.write_acquisition_parameters(str(blocker / "missing"), PARAMETERS).is_failure)


if __name__ == "__main__":
    unittest.main()
