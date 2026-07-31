"""
Electric Field Probe Acquisition Use-Case Error Union

Responsibility:
- Enumerate every terminal failure mode of the continuous EF probe acquisition
  use case that its caller (Presenter, tests) must distinguish.

Rationale:
- The probe streaming loop currently catches `Exception` in infrastructure and
  translates it to a `ElectricFieldProbeReadingFailed` event. This union makes
  the failure surface explicit and typed at the application boundary.

Design:
- Sealed-union pattern via base class + frozen dataclasses.
- Variants named after the refused promise, not the exception class.
"""

from __future__ import annotations

from dataclasses import dataclass


class ProbeAcquisitionError:
    """
    Sealed union tag for EF probe continuous acquisition failures.
    """


@dataclass(frozen=True)
class ProbeNotReady(ProbeAcquisitionError):
    """The probe adapter reports it is not ready to acquire samples."""

    probe_serial_number: str


@dataclass(frozen=True)
class SampleAcquisitionFailed(ProbeAcquisitionError):
    """A single sample acquisition raised; the stream cannot continue."""

    sample_index: int
    error_detail: str
