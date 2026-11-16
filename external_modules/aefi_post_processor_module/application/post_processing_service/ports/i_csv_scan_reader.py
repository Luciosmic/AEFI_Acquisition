from abc import ABC, abstractmethod

from ..dtos.scan_samples_dto import ScanSamplesDTO


class ICsvScanReader(ABC):
    """
    Responsibility:
    - Read a scan CSV file (columns x, y and the voltage channels) into arrays.

    Rationale:
    - The service must not know pandas nor the file system: the scan format is an export detail of the acquisition.

    Design:
    - Outbound port, pure ABC. A missing file raises FileNotFoundError("CSV file not found: <path>").
    - Channels are those of voltage_x/y/z_in_phase/quadrature present in the file, in that order; none present gives an empty channel list.
    """

    @abstractmethod
    def read(self, csv_path: str) -> ScanSamplesDTO:
        """The points of the scan file, as arrays."""
