import numpy as np
import pytest

from ....application.post_processing_service.dtos.scan_samples_dto import ScanSamplesDTO
from ..csv_scan_reader import CsvScanReader
from .csv_scan_reader_contract import CsvScanReaderContract


class TestCsvScanReader(CsvScanReaderContract):
    @pytest.fixture(autouse=True)
    def _folder(self, tmp_path):
        self.folder = tmp_path

    def path_of(self, name):
        return str(self.folder / name)

    def reader_holding(self, name, samples):
        header = ['x', 'y', *samples.channel_names]
        rows = [
            ",".join(repr(float(v)) for v in (x, y, *vals))
            for x, y, vals in zip(samples.x, samples.y, samples.values)
        ]
        (self.folder / name).write_text("\n".join([",".join(header), *rows]) + "\n", encoding="utf-8")
        return CsvScanReader()

    def reader_without_files(self):
        return CsvScanReader()

    def test_columns_are_ordered_like_the_pipeline_expects_whatever_the_file_order(self):
        (self.folder / "shuffled.csv").write_text(
            "voltage_z_in_phase,y,x,voltage_x_in_phase\n9.0,0.0,0.0,1.0\n", encoding="utf-8"
        )

        read = CsvScanReader().read(self.path_of("shuffled.csv"))

        assert tuple(read.channel_names) == ('voltage_x_in_phase', 'voltage_z_in_phase')
        assert np.array_equal(read.values, np.array([[1.0, 9.0]]))
