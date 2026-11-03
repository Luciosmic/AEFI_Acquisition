from dataclasses import dataclass


@dataclass(frozen=True)
class OperatorDTO:
    """An operator as the interface shows it and the export records it."""

    operator_id: str
    name: str


@dataclass(frozen=True)
class OperatorRegistrationDTO:
    """Outcome of a registration: the operator to use, and whether that
    spelling was already known (then the existing operator is returned)."""

    operator: OperatorDTO
    already_registered: bool
