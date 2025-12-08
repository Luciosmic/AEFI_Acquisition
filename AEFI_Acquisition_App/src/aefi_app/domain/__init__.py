"""
Domain layer for AEFI MPh Simulator.

Responsibility:
    Pure business logic with zero external dependencies (no COMSOL, no I/O).

Layer position:
    Domain is the innermost layer. No dependencies on Application or Infrastructure.

Design:
    - value_objects/: Immutable value objects (GridPoint, JobParameters, JobResult, etc.)
    - entities/: Entities with identity and lifecycle (SpatialScan1D, SpatialScan2D, SpatialScan3D)
    - aggregates/: Aggregate roots (Job, Study)
    - services/: Domain services (Evaluator, MetadataBuilder)
    - exceptions.py: Domain-specific exceptions

DDD Principle:
    Domain layer defines the language and rules of the business.
    It should be testable without any infrastructure (mocks, files, databases).

Naming clarification:
    "value_objects" (not "models") avoids confusion with COMSOL model (.mph file).
    Value objects are immutable data structures defined by their values.
"""

from .aggregates import Study
from .entities import Job
from .entities import Scan, SpatialScan1D, SpatialScan2D, SpatialScan3D
from .exceptions import (
    DomainException,
    InvalidSpatialRangeError,
    InvalidScanAxisError,
    InvalidScanTransitionError,
    InvalidJobTransitionError,
    ParameterConflictError,
    ScanNotFoundError,
)
from .value_objects import (
    JobExecutionMetadata,
    JobId,
    JobParameters,
    JobResult,
    JobStatus,
    JobMeshMetadata,
    ScanId,
    ScanStatus,
    ScanPointResult,
    ScanResults,
    ScanExecutionMetadata,
    SolverMetadata,
    StudyId,
    StudyStatus,
    StudyResults,
    StudyExecutionMetadata,
)

__all__ = [
    # Aggregates
    "Job",
    "Study",
    # Entities
    "Scan",
    "SpatialScan1D",
    "SpatialScan2D",
    "SpatialScan3D",
    # Value objects - Job
    "JobExecutionMetadata",
    "JobId",
    "JobParameters",
    "JobResult",
    "JobStatus",
    "JobMeshMetadata",
    # Value objects - Scan
    "ScanId",
    "ScanStatus",
    "ScanPointResult",
    "ScanResults",
    "ScanExecutionMetadata",
    # Value objects - Study
    "StudyId",
    "StudyStatus",
    "StudyResults",
    "StudyExecutionMetadata",
    # Value objects - Other
    "SolverMetadata",
    # Exceptions
    "DomainException",
    "InvalidScanTransitionError",
    "InvalidJobTransitionError",
    "ParameterConflictError",
    "ScanNotFoundError",
    "InvalidSpatialRangeError",
    "InvalidScanAxisError",
]
