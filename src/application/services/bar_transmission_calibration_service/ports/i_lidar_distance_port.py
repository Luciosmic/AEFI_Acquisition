"""
LIDAR Distance Port Interface

Responsibility:
- Open the LIDAR distance stream for the calibration, read distances
  timestamped at their reception, close it.
- Say whether someone else (the inertial sensor panel) streams it already.

Rationale:
- The calibration starts and stops the LIDAR stream itself (decision
  2026-10-15) and must refuse when the panel already streams it: the serial
  link has one owner.

Design:
- open(): LidarStreamBusyError if streamed elsewhere, LidarUnavailableError if
  the link cannot be opened. Connects the link if needed (and close() then
  disconnects it again).
- read_distance(): next reading in reception order, or None on timeout.
  Readings are timestamped when they arrive, not when they are read: a reader
  that waits (settling) can still tell which readings came after the wait.
- Each reading carries a domain LidarDistance: a valid distance (> 0) or "no
  return" (the LIDAR sends 0 when it measures nothing: floor out of range,
  dropout). Only valid distances or explicit "no return" samples: never a
  distance of 0, and never a "no return" dropped silently (off the bar, it is
  the floor's signature). The 0 rule itself lives in LidarDistance.
- close(): idempotent, always stops the stream (the board keeps streaming
  until told to stop).
- Timestamps share the service clock (time.perf_counter on the bench).
"""

from abc import ABC, abstractmethod
from typing import Optional

from application.services.bar_transmission_calibration_service.dtos.bar_transmission_calibration_dtos import (
    LidarDistanceReading,
)


class ILidarDistancePort(ABC):
    @abstractmethod
    def is_streamed_elsewhere(self) -> bool:
        """True while another owner (the sensor panel) streams the board."""

    @abstractmethod
    def open(self) -> None:
        """Start the LIDAR stream for this caller."""

    @abstractmethod
    def read_distance(self, timeout_s: float) -> Optional[LidarDistanceReading]:
        """Next reading in reception order (its LidarDistance may be "no return");
        None on timeout; LidarUnavailableError on link failure."""

    @abstractmethod
    def close(self) -> None:
        """Stop the stream (and disconnect if open() connected). Idempotent."""
