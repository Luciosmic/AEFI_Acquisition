from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)


@dataclass(frozen=True)
class ActiveSensorRotationChanged(DomainEvent):
    """The mounting rotation P applied to sensor readings changed:
    a sensor calibration was recorded, the source geometry changed (fallback
    to the ideal angles), or trial angles are being tuned (not persisted)."""

    angles: SensorRotationAngles
    is_calibrated: bool
    recorded_at: Optional[datetime]
    is_trial: bool = False
