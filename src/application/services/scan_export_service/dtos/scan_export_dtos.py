"""
Scan Export DTOs

Data Transfer Objects for the Scan Export Service.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExportConfigDTO:
    """Configuration for data export."""
    enabled: bool
    output_directory: str
    filename_base: str
    include_metadata: bool = True
    format: str = "CSV"
