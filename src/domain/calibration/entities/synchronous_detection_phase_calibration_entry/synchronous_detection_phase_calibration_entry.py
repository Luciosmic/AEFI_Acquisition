"""
Synchronous Detection Phase Calibration Entry Entity

Responsibility:
- Immutable, append-only record of calibration point(s) measured on a
  given hardware setup.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple
from uuid import UUID, uuid4

from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from domain.calibration.value_objects.synchronous_detection_phase_calibration_point.synchronous_detection_phase_calibration_point import (
    SynchronousDetectionPhaseCalibrationPoint,
)


@dataclass(frozen=True)
class SynchronousDetectionPhaseCalibrationEntry:
    """
    One append-only registry entry: the calibration point(s) recorded on a
    specific hardware setup, at a specific time.

    Entity — identity is `entry_id`, not the values it carries. Immutable
    once created (the registry is constructive: entries are added, never
    edited or removed).
    """

    entry_id: UUID
    hardware_signature: HardwareSignature
    points: Tuple[SynchronousDetectionPhaseCalibrationPoint, ...]
    recorded_at: datetime

    def __post_init__(self):
        if not self.points:
            raise ValueError("A calibration entry must carry at least one point")

    @staticmethod
    def single(
        hardware_signature: HardwareSignature,
        point: SynchronousDetectionPhaseCalibrationPoint,
    ) -> "SynchronousDetectionPhaseCalibrationEntry":
        """Mint a fresh entry wrapping a single freshly measured point."""
        return SynchronousDetectionPhaseCalibrationEntry(
            entry_id=uuid4(),
            hardware_signature=hardware_signature,
            points=(point,),
            recorded_at=datetime.now(timezone.utc),
        )
