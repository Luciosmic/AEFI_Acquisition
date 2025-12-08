"""Domain value objects: Immutable data structures representing domain concepts."""

from . import job
from . import scan
from . import study

__all__ = [
    # Job-related
    "JobParameters",
    "JobResult",
    "JobId",
    "JobStatus",
    "JobExecutionMetadata",
    "SolverMetadata",
    "JobMeshMetadata",
    # Scan-related (universal)
    "ScanId",
    "ScanStatus",
    "ScanPointResult",
    "ScanResults",
    "ScanExecutionMetadata",
    # Scan-related (spatial-specific)
    "AxisDirection",
    "SpatialRange",
    "ScanAxis",
    # Study-related
    "StudyId",
    "StudyStatus",
    "StudyResults",
    "StudyExecutionMetadata",
]

# Re-export from sub-packages (domain/__init__.py imports from here, not from sub-packages)
from .job import (
    JobParameters,
    JobResult,
    JobId,
    JobStatus,
    JobExecutionMetadata,
    SolverMetadata,
    JobMeshMetadata,
)
from .scan import (
    ScanId,
    ScanStatus,
    ScanPointResult,
    ScanResults,
    ScanExecutionMetadata,
    AxisDirection,
    SpatialRange,
    ScanAxis,
)
from .study import (
    StudyId,
    StudyStatus,
    StudyResults,
    StudyExecutionMetadata,
)

