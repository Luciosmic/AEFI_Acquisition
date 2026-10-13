"""
Motion Control Use-Case Error Union

Responsibility:
- Enumerate every failure mode a caller of MotionControlService commands
  must be prepared to distinguish.

Rationale:
- A bench that is not calibrated (no mm/pulse conversion) must be told apart
  from a hardware failure: the first asks the operator to calibrate, the
  second to check the bench. This is the cross-layer translation site, per
  the error-taxonomy standard.

Design:
- Sealed-union pattern: base class + frozen dataclasses.
- `message` is the operator-facing text, so the presenter never inspects
  the variants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class MotionControlError:
    """Sealed union tag for motion command failures visible to the use-case caller."""

    @property
    def message(self) -> str:  # pragma: no cover - overridden by every variant
        raise NotImplementedError

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class MotionConversionUnavailable(MotionControlError):
    """The motion port has no mm/pulse conversion: the command is refused, nothing moved."""

    operation: str
    motor_name: Optional[str] = None
    missing_quantity: Optional[str] = None
    where_to_enter: Optional[str] = None

    @property
    def message(self) -> str:
        what = self.missing_quantity or "conversion mm/impulsion"
        who = f" du moteur « {self.motor_name} »" if self.motor_name else ""
        where = f" — à saisir : {self.where_to_enter}" if self.where_to_enter else ""
        return f"{self.operation} refusé : banc non calibré, {what}{who} manquant(e){where}"


@dataclass(frozen=True)
class MotionCommandFailed(MotionControlError):
    """The motion port or controller raised while executing the command."""

    operation: str
    error_detail: str

    @property
    def message(self) -> str:
        return f"{self.operation} failed: {self.error_detail}"
