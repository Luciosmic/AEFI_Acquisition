"""
CsvScanReader - Reads a scan CSV into arrays with pandas (see csv_scan_reader_intention.md).
"""

import os

import pandas as pd

from ...application.post_processing_service.dtos.scan_samples_dto import ScanSamplesDTO
from ...application.post_processing_service.ports.i_csv_scan_reader import ICsvScanReader

VOLTAGE_COLUMNS = (
    'voltage_x_in_phase', 'voltage_x_quadrature',
    'voltage_y_in_phase', 'voltage_y_quadrature',
    'voltage_z_in_phase', 'voltage_z_quadrature',
)


class CsvScanReader(ICsvScanReader):
    def read(self, csv_path: str) -> ScanSamplesDTO:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        df = pd.read_csv(csv_path)
        channels = tuple(col for col in VOLTAGE_COLUMNS if col in df.columns)
        return ScanSamplesDTO(
            x=df['x'].to_numpy(),
            y=df['y'].to_numpy(),
            values=df[list(channels)].to_numpy(dtype=float),
            channel_names=channels,
        )
