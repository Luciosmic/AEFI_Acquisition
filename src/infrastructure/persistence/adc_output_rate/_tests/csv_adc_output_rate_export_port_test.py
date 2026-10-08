import csv
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import numpy as np

from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    AdcOutputRateCharacterizationDTO,
    AdcOutputRatePointDTO,
    DrdyCaptureDTO,
)
from infrastructure.persistence.adc_output_rate.csv_adc_output_rate_export_port import CsvAdcOutputRateExportPort


def point(osr):
    return AdcOutputRatePointDTO(osr, 49, 0, osr / 4.096e6, osr / 4.096e6, 2e-7, 4.096e6 / osr, 4.096e6)


RESULT = AdcOutputRateCharacterizationDTO(
    points=(point(4096), point(32)), mean_modulator_frequency_hz=4.096e6,
    max_modulator_frequency_relative_deviation=0.0, restored_oversampling_ratio=4096, instrument="DSO-X 2014A",
    export_path=None,
)
CAPTURES = [
    (4096, DrdyCaptureDTO((0.0, 1e-3, 2e-3), 5e-7, "DSO-X 2014A", (0.0, 5e-7), (3.1, 0.0))),
    (32, DrdyCaptureDTO((0.0, 7.8125e-6), 4e-9, "DSO-X 2014A")),
]


class TestCsvAdcOutputRateExportPort(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.port = CsvAdcOutputRateExportPort(Path(self._tmp.name), clock=lambda: datetime(2026, 10, 2, 19, 5, 0))

    def tearDown(self):
        self._tmp.cleanup()

    def test_writes_explicitly_named_files(self):
        folder = Path(self.port.export(RESULT, CAPTURES).value)
        self.assertEqual(folder.name, "2026-10-02_190500_odr-adc-ads131a04-drdy-oscilloscope")
        names = sorted(p.name for p in folder.iterdir())
        self.assertEqual(names, [
            "2026-10-02_190500_odr-drdy_formes-d-onde.npz",
            "2026-10-02_190500_odr-drdy_intervalles-fronts-descendants.csv",
            "2026-10-02_190500_odr-drdy_resume-par-osr.csv",
        ])
        lines = (folder / names[2]).read_text(encoding="utf-8").splitlines()
        rows = list(csv.DictReader(l for l in lines if not l.startswith("#")))
        self.assertEqual([r["oversampling_ratio"] for r in rows], ["4096", "32"])
        with open(folder / names[1], encoding="utf-8") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 3)  # 2 intervals at 4096 + 1 at 32
        self.assertEqual(sorted(np.load(folder / names[0]).files), ["osr_4096_t_s", "osr_4096_v_V"])

    def test_unwritable_location_is_a_failure(self):
        blocker = Path(self._tmp.name) / "not_a_dir"
        blocker.write_text("x")
        self.assertTrue(CsvAdcOutputRateExportPort(blocker).export(RESULT, CAPTURES).is_failure)


if __name__ == "__main__":
    unittest.main()
