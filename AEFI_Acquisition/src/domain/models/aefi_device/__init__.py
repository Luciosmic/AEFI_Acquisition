"""
AefiDevice bounded context (Domain Model).

Responsibility:
- Provide a stable import path for the AefiDevice aggregate and its
  related value objects.
"""

from .aefi_device import AefiDevice, DeviceId
from .value_objects import AefiInteractionPair, QuadSourceGeometry, Quadrant

__all__ = [
    "AefiDevice",
    "DeviceId",
    "AefiInteractionPair",
    "QuadSourceGeometry",
    "Quadrant",
]

