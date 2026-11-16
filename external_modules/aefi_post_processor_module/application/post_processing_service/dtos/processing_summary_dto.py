from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ProcessingSummaryDTO:
    """What a processing run did: the steps it completed, its refusals and the history stored with the steps."""

    steps_completed: Tuple[str, ...]
    errors: Tuple[str, ...]
    success: bool
    output_file: str
    processing_history: Tuple[str, ...]
