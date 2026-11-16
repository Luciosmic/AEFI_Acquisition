from dataclasses import dataclass


@dataclass(frozen=True)
class LoadStepDTO:
    """Which stored step of which acquisition to load as a map."""

    acquisition_file: str
    step_name: str
