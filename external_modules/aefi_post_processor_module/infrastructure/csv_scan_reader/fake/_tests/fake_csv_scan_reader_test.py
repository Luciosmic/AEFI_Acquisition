from .....application.post_processing_service.dtos.scan_samples_dto import ScanSamplesDTO
from ....csv_scan_reader._tests.csv_scan_reader_contract import CsvScanReaderContract
from ..fake_csv_scan_reader import FakeCsvScanReader


class TestFakeCsvScanReader(CsvScanReaderContract):
    def path_of(self, name):
        return f"/fake/{name}"

    def reader_holding(self, name: str, samples: ScanSamplesDTO):
        reader = FakeCsvScanReader()
        reader.add_file(self.path_of(name), samples)
        return reader

    def reader_without_files(self):
        return FakeCsvScanReader()
