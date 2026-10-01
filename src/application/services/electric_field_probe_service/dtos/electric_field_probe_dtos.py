from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ElectricFieldProbeAcquisitionConfig:
    """
    Configuration for electric field probe continuous acquisition.

    - max_duration_s: optional duration limit; None means until explicit stop.

    Acquisition runs best-effort (no sample_rate_hz): the Narda probe's own
    serial round-trip paces the loop.
    """

    max_duration_s: Optional[float] = None


@dataclass(frozen=True)
class FrequencyCorrectionResult:
    """
    Result of a request to apply the probe's frequency-dependent calibration
    correction (see IElectricFieldProbePort.apply_frequency_correction).

    - applied_hz: frequency confirmed by the probe, None if out of range or on error.
    - in_range: False if requested_hz is below the probe's qualified RF range.
    - error: hardware failure message, if any (never a raised exception).
    """

    requested_hz: float
    applied_hz: Optional[float]
    in_range: bool
    error: Optional[str] = None
