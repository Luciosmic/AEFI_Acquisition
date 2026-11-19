"""
CsvScanReader - Reads a scan CSV into arrays with pandas (see csv_scan_reader_intention.md).
"""

import hashlib
import io
import os

import pandas as pd

from ...domain.processing.grid_builder.grid_builder import VOLTAGE_CHANNELS
from ...application.post_processing_service.dtos.scan_samples_dto import ScanSamplesDTO
from ...application.post_processing_service.ports.i_csv_scan_reader import ICsvScanReader


class CsvScanReader(ICsvScanReader):
    def read(self, csv_path: str) -> ScanSamplesDTO:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        with open(csv_path, 'rb') as f:
            content = f.read()
        df = pd.read_csv(io.BytesIO(content))
        channels = tuple(col for col in VOLTAGE_CHANNELS if col in df.columns)
        return ScanSamplesDTO(
            x=df['x'].to_numpy(),
            y=df['y'].to_numpy(),
            values=df[list(channels)].to_numpy(dtype=float),
            channel_names=channels,
            sha256=hashlib.sha256(content).hexdigest(),
        )
