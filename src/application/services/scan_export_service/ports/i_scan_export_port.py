"""
Export Port Interface

Defines the contract for exporting scan data.
Infrastructure layer will implement this (e.g., CSVExporter).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

from application.services.scan_export_service.dtos.scan_acquisition_parameters_dtos import (
    ScanAcquisitionParametersDTO,
)
from domain.shared_kernel.events.domain_event import DomainEvent

class IScanExportPort(ABC):
    """Interface for data export."""

    @abstractmethod
    def configure(
        self,
        directory: str,
        filename: str,
        metadata: Dict[str, Any],
        timestamp: Optional[str] = None,
        acquisition_kind: str = "stepScan",
    ) -> None:
        """Configure the export destination and metadata.

        `timestamp`: shared acquisition-folder timestamp (`YYYY-MM-DD_HHMMSS`).
        Pass the same value to every port driven for one scan so CSV and
        HDF5 land in the same acquisition folder; omit to self-generate
        (single-port callers, tests).
        `acquisition_kind`: folder/file name tag — `stepScan` for a 2D scan,
        `flyScan` for a fly-scan exploration map, `timeSeries` for a
        continuous reading exported vs time.
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
    def write_acquisition_parameters(self, parameters: ScanAcquisitionParametersDTO) -> None:
        """Write the acquisition-parameters document (schema 1.0) from these facts.
        Called at acquisition start (`activity.status == "running"`) and again
        after stop() with the outcome: the final call lists and hashes the
        files produced. Ports that don't own the acquisition folder implement
        it as a no-op."""
        pass

    @abstractmethod
    def write_event(self, event: DomainEvent) -> None:
        """Persist one domain event published during the scan (per-scan event store).
        Ports that don't keep an event store implement it as a no-op."""
        pass

    @abstractmethod
    def get_output_path(self) -> Optional[Path]:
        """Path to this port's main data file, once configured (None before configure())."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop export and close file."""
        pass
