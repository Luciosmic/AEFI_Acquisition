"""
BenchCalibrationData Value Object

Responsibility:
- Capture calibration results linking the physical bench configuration
  (sources, sensor) to derived interaction data (e.g. AefiInteractionPair).

Rationale:
- Provide a stable domain representation of calibration artefacts that
  can be stored/loaded independently of hardware drivers.
"""

from dataclasses import dataclass
from typing import List

from domain.models.aefi_device import AefiInteractionPair


@dataclass(frozen=True)
class BenchCalibrationData:
    """
    Calibration data for the test bench.

    Notes:
    - This is intentionally high-level; details about how the calibration
      is performed or stored on disk belong to application/infrastructure.
    """

    interactions: List[AefiInteractionPair]



