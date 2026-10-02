"""
Scan Export DTOs

Data Transfer Objects for the Scan Export Service.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExportConfigDTO:
    """Configuration for data export. Every scan is exported to both CSV and HDF5."""
    enabled: bool
    output_directory: str
    filename_base: str
    include_metadata: bool = True
    # Written in acquisition-parameters.json (feature_of_interest.description,
    # provenance.operator.name) — empty = declared missing, never guessed.
    measured_object: str = ""
    operator: str = ""
