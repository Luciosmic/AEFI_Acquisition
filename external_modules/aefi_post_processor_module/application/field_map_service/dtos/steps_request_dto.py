from dataclasses import dataclass


@dataclass(frozen=True)
class StepsRequestDTO:
    """Which acquisition to list the stored steps of."""

    acquisition_file: str
