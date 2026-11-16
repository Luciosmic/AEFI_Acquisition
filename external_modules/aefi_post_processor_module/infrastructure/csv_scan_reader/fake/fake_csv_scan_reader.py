"""
FakeCsvScanReader - In-memory scan files (see fake_csv_scan_reader_intention.md).
"""

from typing import Dict

from ....application.post_processing_service.dtos.scan_samples_dto import ScanSamplesDTO
from ....application.post_processing_service.ports.i_csv_scan_reader import ICsvScanReader


class FakeCsvScanReader(ICsvScanReader):
    def __init__(self) -> None:
        self._files: Dict[str, ScanSamplesDTO] = {}

    def add_file(self, csv_path: str, samples: ScanSamplesDTO) -> None:
        self._files[csv_path] = samples

    def read(self, csv_path: str) -> ScanSamplesDTO:
        if csv_path not in self._files:
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        return self._files[csv_path]
