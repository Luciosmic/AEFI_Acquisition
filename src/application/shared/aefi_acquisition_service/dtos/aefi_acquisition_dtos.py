from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AefiAcquisitionConfig:
    """
    Configuration for continuous acquisition.

    - max_duration_s: optional duration limit; None means until explicit stop.

    Acquisition runs best-effort: the real ADC round-trip (OSR x n_avg,
    configured separately in hardware advanced config) dominates timing by
    orders of magnitude, so there is no software-paced sample_rate_hz here.
    """

    max_duration_s: Optional[float] = None
