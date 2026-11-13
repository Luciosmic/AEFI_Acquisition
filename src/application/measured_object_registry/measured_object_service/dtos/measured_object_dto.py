from dataclasses import dataclass


@dataclass(frozen=True)
class MeasuredObjectDTO:
    """An measured_object as the interface shows it and the export records it."""

    measured_object_id: str
    name: str


@dataclass(frozen=True)
class MeasuredObjectRegistrationDTO:
    """Outcome of a registration: the measured_object to use, and whether that
    spelling was already known (then the existing measured_object is returned)."""

    measured_object: MeasuredObjectDTO
    already_registered: bool
