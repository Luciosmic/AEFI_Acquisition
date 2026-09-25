"""
Sensor Calibration Entry Entity

Responsibility:
- Immutable, append-only record of a sensor mounting angle calibration,
  referencing the sensor mounting and the source geometry entry it was
  measured against.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)


@dataclass(frozen=True)
class SensorCalibrationEntry:
    """
    One append-only registry entry: the mounting angles of a sensor, measured
    on one mounting of that sensor (`sensor_mounting_id`, the
    `HardwareComponentSelection` of the sensor) against one source geometry
    (`source_geometry_entry_id`). Both are referenced by identity, never
    copied by value. The electronic boards play no role in the angles.

    Entity — identity is `entry_id`. Immutable once created.
    """

    entry_id: UUID
    sensor_mounting_id: UUID
    source_geometry_entry_id: UUID
    angles: SensorRotationAngles
    recorded_at: datetime

    @staticmethod
    def single(
        sensor_mounting_id: UUID,
        source_geometry_entry_id: UUID,
        angles: SensorRotationAngles,
    ) -> "SensorCalibrationEntry":
        """Mint a fresh entry wrapping a freshly measured set of angles."""
        return SensorCalibrationEntry(
            entry_id=uuid4(),
            sensor_mounting_id=sensor_mounting_id,
            source_geometry_entry_id=source_geometry_entry_id,
            angles=angles,
            recorded_at=datetime.now(timezone.utc),
        )
