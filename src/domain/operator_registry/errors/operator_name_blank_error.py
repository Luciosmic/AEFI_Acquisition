"""
Operator Name Blank Error — refused promise "an operator has a name"
(see operator_name_blank_error_intention.md).
"""


class OperatorNameBlankError(ValueError):
    """An operator cannot be registered without a name."""
