"""
Bar Profile Unusable Error

See bar_profile_unusable_error_intention.md.
"""


class BarProfileUnusableError(ValueError):
    """The fly scan profile does not show one bar, fully inside the travel, with
    floor on both sides."""
