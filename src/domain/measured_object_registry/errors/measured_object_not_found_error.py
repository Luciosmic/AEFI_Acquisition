"""
MeasuredObject Not Found Error — refused promise "the measured object to change is in the
registry" (see measured_object_not_found_error_intention.md).
"""


class MeasuredObjectNotFoundError(LookupError):
    """No measured object of this identity in the registry (already deleted, or never registered)."""
