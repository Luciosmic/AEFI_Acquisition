from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ElectricFieldProbeAcquisitionConfig:
    """
    Configuration for electric field probe continuous acquisition.

    - sample_rate_hz: target acquisition rate.
    - max_duration_s: optional duration limit; None means until explicit stop.
    """

    sample_rate_hz: float
    max_duration_s: Optional[float] = None
