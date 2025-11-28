"""
Domain entities.

This module contains entities (objects with identity and lifecycle).
Entities are mutable objects that are defined by their identity rather than
their attributes.
"""

from .job import Job
from .spatial_scan import (
    Scan,
    SpatialScan1D,
    SpatialScan2D,
    SpatialScan3D,
)

__all__ = [
    "Job",
    "Scan",
    "SpatialScan1D",
    "SpatialScan2D",
    "SpatialScan3D",
]
