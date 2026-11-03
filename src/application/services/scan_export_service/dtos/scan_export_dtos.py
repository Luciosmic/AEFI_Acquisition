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
    # provenance.operator {id, name}) — empty = declared missing, never guessed.
    # The operator comes from the operators registry (OperatorService).
    measured_object: str = ""
    operator_id: str = ""
    operator: str = ""
