"""
MeasuredObject Name Taken Error — refused promise "one measured object, one spelling"
on a rename (see measured_object_name_taken_error_intention.md).
"""


class MeasuredObjectNameTakenError(ValueError):
    """Another measured object already has this spelling (case and spacing insensitive)."""
