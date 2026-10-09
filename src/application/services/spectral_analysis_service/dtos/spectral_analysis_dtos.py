from dataclasses import dataclass


@dataclass(frozen=True)
class SetWindowDurationDTO:
    """Window duration (seconds) for the continuous FFT buffer. Changing it
    clears the current buffer (no partial-window carry-over)."""

    seconds: float
