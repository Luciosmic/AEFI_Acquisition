"""
Domain: Custom exceptions for domain logic.

Responsibility:
    Define domain-specific exceptions for clear error handling.

Rationale:
    Using custom exceptions makes domain errors explicit and distinguishable
    from infrastructure or framework errors. This improves debugging and
    allows application layer to handle domain errors appropriately.

Design:
    - Base DomainException for all domain errors
    - Specific exceptions for different domain violations
    - No infrastructure dependencies
"""

from __future__ import annotations


class DomainException(Exception):
    """Base exception for all domain-related errors.

    All domain exceptions should inherit from this class to allow
    catching all domain errors with a single except clause if needed.
    """
    pass


class InvalidScanTransitionError(DomainException):
    """Raised when attempting an invalid scan state transition.

    Example: Trying to mark a COMPLETED scan as RUNNING.
    """
    pass


class ParameterConflictError(DomainException):
    """Raised when there's a conflict in parameter usage across scans.

    Example: Trying to create a new position scan while another is still active.
    """
    pass


class ScanNotFoundError(DomainException):
    """Raised when a scan cannot be found by its ID.

    Example: Trying to retrieve a scan that doesn't exist in the study.
    """
    pass


class InvalidSpatialRangeError(DomainException):
    """Raised when position range parameters are invalid.

    Example: min_value >= max_value, or num_points < 2.
    """
    pass


class InvalidScanAxisError(DomainException):
    """Raised when scan axis configuration is invalid.

    Example: Using angle_rad with non-ANGULAR direction.
    """
    pass


class InvalidJobTransitionError(DomainException):
    """Raised when attempting an invalid job status transition.

    Example: Trying to mark a COMPLETED job as RUNNING, or marking as COMPLETED
    from PENDING without going through RUNNING first.
    """
    pass