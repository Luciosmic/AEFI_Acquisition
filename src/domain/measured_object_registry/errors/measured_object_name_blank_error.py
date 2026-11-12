"""
MeasuredObject Name Blank Error — refused promise "an measured_object has a name"
(see measured_object_name_blank_error_intention.md).
"""


class MeasuredObjectNameBlankError(ValueError):
    """An measured_object cannot be registered without a name."""
