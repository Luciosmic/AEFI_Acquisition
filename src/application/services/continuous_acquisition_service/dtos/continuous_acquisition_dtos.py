from dataclasses import dataclass
from typing import Optional

from domain.value_objects.measurement_uncertainty import MeasurementUncertainty


@dataclass(frozen=True)
class ContinuousAcquisitionConfig:
    """
    Configuration for continuous acquisition.

    - sample_rate_hz: target acquisition rate (None = hardware default).
    - max_duration_s: optional duration limit; None means until explicit stop.
    - target_uncertainty: optional measurement quality target.
    """

    sample_rate_hz: Optional[float] = None
    max_duration_s: Optional[float] = None
    target_uncertainty: Optional[MeasurementUncertainty] = None
