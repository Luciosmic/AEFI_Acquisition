from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SourceRecordDTO:
    """The scan file a processing came from: its path, the SHA-256 of what was read, and what the acquisition
    recorded about it (None when no description says)."""

    csv_path: str
    sha256: Optional[str] = None
    activity_id: Optional[str] = None
    declared_sha256: Optional[str] = None

    @property
    def matches_declared(self) -> Optional[bool]:
        """Whether the CSV read is the one the acquisition hashed; None when the acquisition declared no hash."""
        if self.declared_sha256 is None or self.sha256 is None:
            return None
        return self.sha256 == self.declared_sha256
