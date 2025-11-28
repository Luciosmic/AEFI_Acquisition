"""
Domain: Spatial range value objects for spatial scans.

Responsibility:
    Define axis directions and spatial ranges for 1D/2D/3D scans.

Rationale:
    Spatial scans are a core domain concept in experimental measurements.
    These value objects capture the "what" (axis, range) without the "how"
    (implementation details of generating the actual spatial positions).

Design:
    - Immutable value objects (frozen dataclasses)
    - Self-validating (invariants checked in __post_init__)
    - No infrastructure dependencies
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ...exceptions import InvalidSpatialRangeError, InvalidScanAxisError


class AxisDirection(Enum):
    """Direction of a 1D spatial scan.

    Values
    ------
    X : str
        Scan along X axis (y and z fixed).
    Y : str
        Scan along Y axis (x and z fixed).
    Z : str
        Scan along Z axis (x and y fixed).
    ANGULAR : str
        Scan along an angular line in XY plane passing through origin.
        The relationship is: y = x * tan(theta), z fixed.
    """

    X = "x"
    Y = "y"
    Z = "z"
    ANGULAR = "angular"


@dataclass(frozen=True)
class ScanAxis:
    """Value object: defines the axis for a 1D spatial scan.

    Attributes
    ----------
    direction : AxisDirection
        The direction of the scan (X, Y, Z, or ANGULAR).
    angle_rad : float
        Angle in radians for ANGULAR scans. Must be in [-π, π].
        Must be 0.0 for non-ANGULAR directions.

    Design
    ------
    For X, Y, Z: scan along a single Cartesian axis.
    For ANGULAR: scan along a line y = x*tan(angle_rad) in the XY plane.

    Invariants
    ----------
    - If direction is ANGULAR, angle_rad must be in [-π, π]
    - If direction is not ANGULAR, angle_rad must be 0.0

    Examples
    --------
    >>> axis_x = ScanAxis(direction=AxisDirection.X)
    >>> axis_angular = ScanAxis(direction=AxisDirection.ANGULAR, angle_rad=0.785)  # 45°
    """

    direction: AxisDirection
    angle_rad: float = 0.0

    def __post_init__(self) -> None:
        """Validate axis configuration.

        Raises
        ------
        InvalidScanAxisError
            If angle_rad is invalid for the given direction.
        """
        if self.direction == AxisDirection.ANGULAR:
            if not (-3.14159 <= self.angle_rad <= 3.14159):
                raise InvalidScanAxisError(
                    f"Angle {self.angle_rad} rad must be in [-π, π] for ANGULAR scans"
                )
        elif self.angle_rad != 0.0:
            raise InvalidScanAxisError(
                f"Angle must be 0.0 for {self.direction.value} direction, got {self.angle_rad}"
            )

    def __str__(self) -> str:
        """Return human-readable string representation.

        Returns
        -------
        str
            String like "X", "Y", "Z", or "Angular(θ=0.79rad)".
        """
        if self.direction == AxisDirection.ANGULAR:
            return f"Angular(θ={self.angle_rad:.2f}rad)"
        return self.direction.value.upper()


@dataclass(frozen=True)
class SpatialRange:
    """Value object: defines a range of spatial positions for scanning.

    Attributes
    ----------
    min_value : float
        Minimum spatial position value.
    max_value : float
        Maximum spatial position value.
    num_points : int
        Number of points to generate in this range (≥2).
    unit : str
        Physical unit (e.g., "cm", "mm", "m").

    Design
    ------
    Represents the configuration for generating a linear sequence of spatial positions.
    Does not contain the actual spatial positions (that's infrastructure concern).

    Invariants
    ----------
    - min_value < max_value
    - num_points ≥ 2 (need at least start and end)

    Examples
    --------
    >>> range_x = SpatialRange(min_value=-10.0, max_value=0.0, num_points=51, unit="cm")
    >>> # Represents: 51 points from -10cm to 0cm
    """

    min_value: float
    max_value: float
    num_points: int
    unit: str

    def __post_init__(self) -> None:
        """Validate spatial range parameters.

        Raises
        ------
        InvalidSpatialRangeError
            If min_value >= max_value or num_points < 2.
        """
        if self.min_value >= self.max_value:
            raise InvalidSpatialRangeError(
                f"min_value ({self.min_value}) must be < max_value ({self.max_value})"
            )
        if self.num_points < 2:
            raise InvalidSpatialRangeError(
                f"num_points ({self.num_points}) must be ≥ 2"
            )

    def span(self) -> float:
        """Calculate the span of the range.

        Returns
        -------
        float
            max_value - min_value
        """
        return self.max_value - self.min_value

    def step_size(self) -> float:
        """Calculate the step size between consecutive points.

        Returns
        -------
        float
            (max_value - min_value) / (num_points - 1)
        """
        return self.span() / (self.num_points - 1)
