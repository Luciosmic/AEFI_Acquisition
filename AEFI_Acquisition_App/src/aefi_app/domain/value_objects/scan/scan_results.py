"""
Domain: Scan results value object.

Responsibility:
    Represent the complete results of a scan.
    Organizes scan point results into a coherent scan result structure.
    Universal concept applicable to all scan types (spatial, frequency, etc.).

Rationale:
    A scan produces multiple point results (one per scan point).
    This value object encapsulates the collection of point results,
    maintaining the relationship between scan points and their results.
    Separates the domain concept of "scan results" from the entity's state.

    Uses ScanPointResult (scan-level concept) rather than JobResult
    (execution-level concept) to maintain clean separation between
    scan abstraction and execution strategy.

Design:
    - Immutable value object (frozen dataclass)
    - Contains ordered list of ScanPointResult (one per scan point)
    - Associated with a ScanId for traceability
    - No dependencies on job or execution concepts
    - Universal: used by SpatialScan, FrequencyScan, etc.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .scan_point_result import ScanPointResult
from .scan_id import ScanId


@dataclass(frozen=True)
class ScanResults:
    """Value object: complete results of a scan.

    Universal results container applicable to all scan types.

    Attributes
    ----------
    scan_id : ScanId
        Unique identifier of the scan these results belong to.
    point_results : List[ScanPointResult]
        Ordered list of point results, one per scan point.
        Index i corresponds to the i-th scan point.

    Design
    ------
    Immutable value object. Represents the complete output of a scan.
    The order of point_results matches the order of scan points.

    Uses ScanPointResult to maintain scan-level abstraction,
    independent of execution strategy (jobs, streaming, etc.).

    Universal: works for spatial scans, frequency scans, etc.

    Invariants
    ----------
    - point_results is not empty (scan must have at least one point)
    - All ScanPointResult instances are valid (validation happens at creation)

    Examples
    --------
    >>> scan_id = ScanId()
    >>> results = ScanResults(
    ...     scan_id=scan_id,
    ...     point_results=[point_result_1, point_result_2, ...]
    ... )
    """

    scan_id: ScanId
    point_results: List[ScanPointResult]
    
    def __post_init__(self) -> None:
        """Validate scan results.

        Raises
        ------
        ValueError
            If point_results is empty.
        """
        if not self.point_results:
            raise ValueError(
                f"Scan results for {self.scan_id} must contain at least one point result"
            )
    
    def get_number_of_results(self) -> int:
        """Return the number of point results.

        Returns
        -------
        int
            Number of point results (equals number of scan points).
        """
        return len(self.point_results)

    def get_result_at_index(self, index: int) -> ScanPointResult:
        """Get the point result at a specific scan point index.

        Parameters
        ----------
        index : int
            Scan point index (0 to count() - 1).

        Returns
        -------
        ScanPointResult
            Point result for the specified scan point.

        Raises
        ------
        IndexError
            If index is out of range.
        """
        if not (0 <= index < len(self.point_results)):
            raise IndexError(
                f"Index {index} out of range for scan {self.scan_id} "
                f"(expected 0 to {len(self.point_results) - 1})"
            )
        return self.point_results[index]

    def get_all_results(self) -> List[ScanPointResult]:
        """Get all point results in order.

        Returns
        -------
        List[ScanPointResult]
            All point results, ordered by scan point index.
        """
        return list(self.point_results)
    
    def is_complete(self, expected_count: int) -> bool:
        """Check if results are complete for the expected number of points.

        Parameters
        ----------
        expected_count : int
            Expected number of scan points.

        Returns
        -------
        bool
            True if count() == expected_count.
        """
        return len(self.point_results) == expected_count

