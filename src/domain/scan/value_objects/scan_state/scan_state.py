"""ScanState lifecycle (see scan_state_intention.md)."""

from enum import Enum


class ScanState(Enum):
    PENDING = "pending"
    STARTED = "started"
    COMPLETED = "completed"
