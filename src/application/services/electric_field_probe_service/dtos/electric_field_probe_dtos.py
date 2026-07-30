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
