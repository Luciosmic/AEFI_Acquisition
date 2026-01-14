"""
Shared Quaternion value object.

Responsibility:
- Expose a rotation type used by AefiDevice (and potentially TestBench)
  through a stable shared-kernel import path.

Implementation Detail:
- Currently re-exports the Quaternion implementation from the AefiDevice
  value_objects package.
"""

from domain.value_objects.aefi_device.quaternion import Quaternion

__all__ = ["Quaternion"]


