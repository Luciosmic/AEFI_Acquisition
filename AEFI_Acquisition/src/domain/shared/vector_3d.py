"""
Shared Vector3D value object.

Responsibility:
- Provide a canonical 3D vector type for all bounded contexts.

Implementation Detail:
- For now, this re-exports the geometric `Vector3D` implementation, which
  remains the single source of truth for the underlying behaviour.
"""

from domain.value_objects.geometric.vector_3d import Vector3D

__all__ = ["Vector3D"]


