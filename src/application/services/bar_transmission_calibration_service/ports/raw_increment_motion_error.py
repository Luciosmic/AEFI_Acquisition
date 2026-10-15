"""
Raw Increment Motion Error

Responsibility:
- The one error IRawIncrementMotionPort declares: the controller or its link
  failed (or a wait timed out) while driving an axis in increments.

Design:
- Raised by the adapter in place of any driver exception; translated by
  BarTransmissionCalibrationService into its use-case error union.
"""


class RawIncrementMotionError(RuntimeError):
    """The bench axis could not be driven in increments."""
