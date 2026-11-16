from dataclasses import dataclass


@dataclass(frozen=True)
class ListAcquisitionsDTO:
    """Which export folder to list, and whether to treat every processed acquisition as stale."""

    export_folder: str
    force: bool = False
