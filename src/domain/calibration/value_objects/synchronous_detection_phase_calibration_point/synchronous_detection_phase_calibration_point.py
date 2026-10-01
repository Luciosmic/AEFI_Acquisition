"""
Synchronous Detection Phase Calibration Point Value Object

Responsibility:
- Associate an excitation frequency with the signed Delta_Phi (ch3 - ch1)
  measured at that frequency.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SynchronousDetectionPhaseCalibrationPoint:
    """
    One measured (frequency, Delta_Phi) pair.

    `delta_phi_degrees` is a signed delta, not an absolute `PhaseAngle` —
    it is not wrapped to [0, 360).
    """

    frequency_hz: float
    delta_phi_degrees: float

    def __post_init__(self):
        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be strictly positive")
