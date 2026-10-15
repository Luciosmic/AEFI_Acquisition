from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class InertialSensorSampleAcquired(DomainEvent):
    """
    A new inertial sensor sample is available.

    Units (UCUM): acceleration_g `[g]`, angular_rate_dps `deg/s`,
    magnetic_field_ut `uT`, lidar_distance_mm `mm`. timestamp_s: reception
    instant on the PC, seconds of a monotonic clock (not wall-clock time).
    """

    acquisition_id: UUID
    sample_index: int
    timestamp_s: float
    acceleration_g: Optional[Tuple[float, float, float]] = None
    angular_rate_dps: Optional[Tuple[float, float, float]] = None
    magnetic_field_ut: Optional[Tuple[float, float, float]] = None
    # ponytail: a distance, not an inertial quantity — carried here only because the
    # lidar travels in the same stream (same board, same serial link). Ceiling: one
    # event carries both. Upgrade: a separate lidar concept and event.
    lidar_distance_mm: Optional[float] = None
