"""
Domain: Scan identity value object.

Responsibility:
    Uniquely identify a scan within a parametric study.
    Universal concept applicable to all scan types (spatial, frequency, etc.).

Rationale:
    Using a dedicated value object for identity (rather than raw UUID)
    makes the domain model more expressive and type-safe. It prevents
    accidentally mixing up scan IDs with other UUIDs.

Design:
    - Immutable (frozen dataclass)
    - Wraps a UUID
    - Two instances with same UUID value are equal
    - No infrastructure dependencies
    - Universal: used by SpatialScan, FrequencyScan, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ScanId:
    """Value object: unique identity of a scan.

    Universal identity applicable to all scan types.

    Attributes
    ----------
    value : UUID
        The unique identifier. Auto-generated if not provided.

    Design
    ------
    Immutable value object. Comparison is by value (UUID), not reference.
    Used by all scan types: SpatialScan, FrequencyScan, etc.
    """

    value: UUID = field(default_factory=uuid4)

    def __str__(self) -> str:
        """Return string representation of the scan ID.

        Returns
        -------
        str
            String representation of the UUID.
        """
        return str(self.value)

    def __repr__(self) -> str:
        """Return developer-friendly representation.

        Returns
        -------
        str
            Representation showing the class and UUID.
        """
        return f"ScanId({self.value})"
