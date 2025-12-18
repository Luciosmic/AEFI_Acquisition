"""
Value Objects specific to the AefiDevice bounded context.

This module re-exports the existing implementations from
`domain.value_objects.aefi_device` to provide a model-level
import path:

    from domain.model.aefi_device.value_objects import QuadSourceGeometry, AefiInteractionPair
"""

from domain.models.aefi_device.value_objects.aefi_interaction_pair import AefiInteractionPair
from domain.models.aefi_device.value_objects.quad_source_geometry import (
    QuadSourceGeometry,
    Quadrant,
)

__all__ = [
    "AefiInteractionPair",
    "QuadSourceGeometry",
    "Quadrant",
]



