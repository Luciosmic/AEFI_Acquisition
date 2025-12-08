"""
Export Port Interface

Defines the contract for exporting scan data.
Infrastructure layer will implement this (e.g., CSVExporter).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class IExportPort(ABC):
    """Interface for data export."""
    
    @abstractmethod
    def configure(self, directory: str, filename: str, metadata: Dict[str, Any]) -> None:
        """Configure the export destination and metadata."""
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
    def stop(self) -> None:
        """Stop export and close file."""
        pass
