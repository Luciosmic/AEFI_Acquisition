"""
MeasuredObject Service Errors — the closed union of what the measured_object use cases
may refuse (see measured_object_service_intention.md).
"""

from dataclasses import dataclass


class MeasuredObjectServiceError:
    """Sealed union tag. Use one of the subclasses."""


@dataclass(frozen=True)
class MeasuredObjectNameBlank(MeasuredObjectServiceError):
    """An measured_object has a name: the typed name was empty."""

    message: str = "un objet mesuré a un nom : saisie vide refusée"


@dataclass(frozen=True)
class MeasuredObjectRegistryUnavailable(MeasuredObjectServiceError):
    """The registry could not be read or written — nothing was changed."""

    reason: str


@dataclass(frozen=True)
class MeasuredObjectNameTaken(MeasuredObjectServiceError):
    """Another measured_object already has this spelling: the rename was refused."""

    message: str


@dataclass(frozen=True)
class MeasuredObjectNotFound(MeasuredObjectServiceError):
    """No measured_object of this identity in the registry — nothing was changed."""

    measured_object_id: str
    message: str = "cet objet mesuré n'est plus dans le registre"
