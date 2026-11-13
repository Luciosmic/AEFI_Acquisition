"""Acquisition name (see acquisition_name_intention.md)."""

from typing import Optional

MISSING_MEASURED_OBJECT = "objet-non-saisi"
MISSING_LIFT_OFF = "liftoff-non-saisi"


def acquisition_name(measured_object: str, lift_off_mm: Optional[float]) -> str:
    """`<measured object>_liftoff-<value>mm`, the part of the exported names after
    `<timestamp>_<stepScan|flyScan|timeSeries>_` (added by the export ports).

    Spaces become dashes; characters a file name cannot carry are dropped. A value
    not entered is written as such, so every name has the same fields.
    """
    words = "-".join((measured_object or "").split())
    measured = "".join(c for c in words if c.isalnum() or c in "-_.") or MISSING_MEASURED_OBJECT
    lift_off = MISSING_LIFT_OFF if lift_off_mm is None else f"liftoff-{lift_off_mm:g}mm"
    return f"{measured}_{lift_off}"
