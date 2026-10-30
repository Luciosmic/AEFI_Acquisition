"""
LIDAR Stream Errors

Responsibility:
- The errors ILidarDistancePort declares: the stream is owned by someone else
  (LidarStreamBusyError), or the link failed (LidarUnavailableError).

Design:
- Raised by the adapter in place of serial/driver exceptions; translated by
  the consuming application service into its use-case error union.
"""


class LidarUnavailableError(RuntimeError):
    """The LIDAR stream could not be opened or read."""


class LidarStreamBusyError(LidarUnavailableError):
    """Another owner (the inertial sensor panel) already streams the board."""
