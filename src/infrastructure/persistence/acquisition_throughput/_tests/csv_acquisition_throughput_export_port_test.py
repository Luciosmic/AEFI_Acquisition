import csv
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputCharacterizationDTO,
    AcquisitionThroughputPointDTO,
    AcquisitionThroughputSampleDTO,
)
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


class TestCsvAcquisitionThroughputExportPort(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.port = CsvAcquisitionThroughputExportPort(base_output_dir=Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_writes_summary_and_samples_in_a_dated_folder(self):
        result = self.port.export(RESULT, SAMPLES)

        self.assertTrue(result.is_success)
        folder = Path(result.value)
        self.assertIn("mcuThroughput_osr4096_excitation-coupée", folder.name)
        summary_lines = (folder / "summary.csv").read_text(encoding="utf-8").splitlines()
        self.assertTrue(any("recommended_n_avg,8" in line for line in summary_lines if line.startswith("#")))
        rows = list(csv.DictReader(line for line in summary_lines if not line.startswith("#")))
        self.assertEqual([r["n_avg"] for r in rows], ["1", "8"])
        with open(folder / "samples.csv", encoding="utf-8") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 6)

    def test_unwritable_location_is_a_failure(self):
        blocker = Path(self._tmp.name) / "not_a_dir"
        blocker.write_text("x")
        port = CsvAcquisitionThroughputExportPort(base_output_dir=blocker)
        self.assertTrue(port.export(RESULT, SAMPLES).is_failure)


if __name__ == "__main__":
    unittest.main()
