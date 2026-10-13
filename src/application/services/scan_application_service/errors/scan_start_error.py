"""
Scan Start Use-Case Error Union

Responsibility:
- Enumerate every reason the scan use case refuses to START, so the caller
  (presenter, panel) can tell the operator what to do.

Rationale:
- `execute_scan` answers a bare bool; a refusal because the bench is not
  calibrated (no mm/pulse conversion) must not read as a generic failure
  "check the logs".

Design:
- Sealed-union pattern: base class + frozen dataclasses, `message` is the
  operator-facing text.
- Distinct from ScanExecutionError (failures once the scan is running).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class ScanStartError:
    """Sealed union tag for scan start refusals visible to the use-case caller."""

    @property
    def message(self) -> str:  # pragma: no cover - overridden by every variant
        raise NotImplementedError

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class ScanRefusedBenchNotCalibrated(ScanStartError):
    """The motion port has no mm/pulse conversion: no scan can be positioned."""

    motor_name: Optional[str] = None
    missing_quantity: Optional[str] = None
    where_to_enter: Optional[str] = None

    @property
    def message(self) -> str:
        what = self.missing_quantity or "conversion mm/impulsion"
        who = f" du moteur « {self.motor_name} »" if self.motor_name else ""
        where = f" — à saisir : {self.where_to_enter}" if self.where_to_enter else ""
        return f"Scan refusé : banc non calibré, {what}{who} manquant(e){where}"
