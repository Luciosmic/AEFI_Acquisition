from dataclasses import dataclass


@dataclass(frozen=True)
class AcquisitionOutcomeDTO:
    """How the processing of one acquisition ended, reported by whoever ran it."""

    name: str
    succeeded: bool
    message: str = ""
