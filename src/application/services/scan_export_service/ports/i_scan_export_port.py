"""
Export Port Interface

Defines the contract for exporting scan data.
Infrastructure layer will implement this (e.g., CSVExporter).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

class IScanExportPort(ABC):
    """Interface for data export."""

    @abstractmethod
    def configure(
        self,
        directory: str,
        filename: str,
        metadata: Dict[str, Any],
        timestamp: Optional[str] = None,
    ) -> None:
        """Configure the export destination and metadata.

        `timestamp`: shared acquisition-folder timestamp (`YYYY-MM-DD_HHMMSS`).
        Pass the same value to every port driven for one scan so CSV and
        HDF5 land in the same acquisition folder; omit to self-generate
        (single-port callers, tests).
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """Start the export process (open file, write header)."""
        pass

    @abstractmethod
    def write_point(self, data: Dict[str, Any]) -> None:
        """Write a single data point."""
        pass

    @abstractmethod
    def write_metadata(self, metadata: Dict[str, Any]) -> None:
        """Write a JSON snapshot of the acquisition's parameters, once per scan."""
        pass

    @abstractmethod
    def get_output_path(self) -> Optional[Path]:
        """Path to this port's main data file, once configured (None before configure())."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop export and close file."""
        pass
