"""
Operator Service Errors — the closed union of what the operator use cases
may refuse (see operator_service_intention.md).
"""

from dataclasses import dataclass


class OperatorServiceError:
    """Sealed union tag. Use one of the subclasses."""


@dataclass(frozen=True)
class OperatorNameBlank(OperatorServiceError):
    """An operator has a name: the typed name was empty."""

    message: str = "un opérateur a un nom : saisie vide refusée"


@dataclass(frozen=True)
class OperatorRegistryUnavailable(OperatorServiceError):
    """The registry could not be read or written — nothing was changed."""

    reason: str
